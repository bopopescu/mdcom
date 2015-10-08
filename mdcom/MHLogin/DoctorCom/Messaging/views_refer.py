
import re
import mimetypes
import magic
import thread
import uuid
import datetime
import json

from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.Messaging.forms import ReferEditForm, ReferClinicalForm,\
	ReferDemographicsForm, ReferInsuranceForm, MessageReferForm
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient, MessageRefer,\
	MessageAttachment
from MHLogin.DoctorCom.Messaging.utils import updateRefer
from MHLogin.DoctorCom.Messaging.utils_new_message import generate_pdf
from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.models import OwnerPublicKey
from MHLogin.KMS.shortcuts import encrypt_object
from MHLogin.KMS.utils import get_user_key
from MHLogin.MHLUsers.models import Physician, MHLUser, Provider, Office_Manager
from MHLogin.MHLUsers.utils import all_staff_members, set_practice_members_result,get_fullname
from MHLogin.MHLOrganization.utils import get_common_org_ids, get_more_providers
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils import FileHelper, ImageHelper
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.errlib import err500, err403
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.DicomHelper import sendToDicomServer
from MHLogin.utils.templates import get_context, get_prefer_logo
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, \
	REFER_FORWARD_CHOICES_ONLY_MANAGER


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/views_refer.log' % 
	(settings.LOGGING_ROOT), 'DoctorCom.Messaging.views_refer', settings.LOGGING_LEVEL)


REFER_CACHE_SESSION_KEY = "ReferData"
PREVENT_REPEAT_COMMIT_TOKEN = "PREVENT_REPEAT_COMMIT_TOKEN"
suffix_re = re.compile('\.([^.]+)$')
MESSAGE_REPEAT_COMMIT = _("Sorry, your refer was sent failed because of duplicate sending.")


def refer_home(request):
	context = get_context(request)

	sender = None
	if ('Provider' in request.session['MHL_Users']):
		sender = request.session['MHL_Users']['Provider']
	elif ('OfficeStaff' in request.session['MHL_Users']):
		sender = request.session['MHL_Users']['OfficeStaff']
	if sender is None:
		return err403(request)

	mhluser = request.session['MHL_Users']['MHLUser']
	sender_id = mhluser.id
	recipient_id = request.REQUEST.get("user_recipients", None)
	if not recipient_id:
		return HttpResponseRedirect('/')

	recipient_provider = None
	try:
		recipient_provider = Provider.objects.get(pk=recipient_id)
	except:
		return err403(request, err_msg=_("This recipient is not a Provider."))

	recipient_pracs = recipient_provider.practices.filter(
				organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
	if len(recipient_pracs) <= 0:
		return err403(request, err_msg=_("This Provider has no organization that can be selected."))

	common_org_ids = get_common_org_ids(sender_id, recipient_id)
	selected_prac_id_init = common_org_ids[0] if common_org_ids else None

	if selected_prac_id_init is None:
		selected_prac_id_init = recipient_pracs[0].id

	cli_form, dem_form, ins_form = get_refer_info(request, context)
	if request.method == "POST":
		if not PREVENT_REPEAT_COMMIT_TOKEN in request.session\
			or not request.session[PREVENT_REPEAT_COMMIT_TOKEN]:
			context['user_recipients'] = recipient_id
#			context['message'] = MESSAGE_REPEAT_COMMIT
			return render_to_response('DoctorCom/Messaging/refer_success.html', context)
		if (cli_form.is_valid() and dem_form.is_valid() and\
				ins_form.is_valid()):
			form_data = cli_form.cleaned_data
			form_data.update(dem_form.cleaned_data)
			form_data.update(ins_form.cleaned_data)
			cur_prac = sender.current_practice
			sel_practice = int(form_data['selected_practice'])
			if common_org_ids and len(common_org_ids) > 0:
				return save_refer(request, form_data, recipient_provider, context)

			phys = list(Physician.objects.filter(user=recipient_provider))
			if len(phys) <= 0 or not phys[0].specialty:
				return save_refer(request, form_data, recipient_provider, context)

			base_geo = None
			if cur_prac:
				base_geo = {
						"longit": cur_prac.practice_longit,
						"lat": cur_prac.practice_lat,
						"base_flag": 1
					}
			else:
				base_geo = {
						"longit": sender.user.longit,
						"lat": sender.user.lat,
						"base_flag": 2
					}
			more_providers = get_more_providers(
					mhluser.id,
					phys[0].specialty,
					base_geo=base_geo)

			if not more_providers or len(more_providers) <= 0:
				return save_refer(request, form_data, recipient_provider, context)

			form_data["file_list"] = get_file_list(request)
			request.session[REFER_CACHE_SESSION_KEY] = form_data
			context['providers'] = more_providers
			context['recipient'] = get_fullname(recipient_provider)
			context['user_photo'] = ImageHelper.get_image_by_type(
					recipient_provider.photo, type="Provider")
			context['sel_practice'] = sel_practice
			context['user_recipients'] = recipient_id

			return render_to_response(
				'DoctorCom/Messaging/refer_more_providers.html',
				context)
	else:
		request.session[PREVENT_REPEAT_COMMIT_TOKEN] = uuid.uuid4().hex

	get_recipient_info(request, recipient_provider, mhluser.mobile_phone, context,\
			recipient_pracs, selected_practice_id=selected_prac_id_init)
	return render_to_response('DoctorCom/Messaging/refer.html', context)


def proceed_save_refer(request):
	context = get_context(request)
	if not REFER_CACHE_SESSION_KEY in request.session\
		or not request.session[REFER_CACHE_SESSION_KEY]:
		context['user_recipients'] = request.REQUEST.get("user_recipients", None)
#		context['message'] = MESSAGE_REPEAT_COMMIT
		return render_to_response('DoctorCom/Messaging/refer_success.html', context)

	refer_data = request.session[REFER_CACHE_SESSION_KEY]

	file_list = None
	if "file_list" in refer_data and refer_data["file_list"]:
		file_list = refer_data["file_list"]
	recipient_id = refer_data["user_recipients"]
	recipient_provider = None
	try:
		recipient_provider = Provider.objects.get(pk=recipient_id)
	except:
		return err403(request, err_msg=_("This recipient is not a Provider."))

	return save_refer(request, refer_data, recipient_provider, context, file_list=file_list)


def check_send_refer(request):
	recipient_id = request.REQUEST.get("user_recipients", None)
	sel_practice = request.REQUEST.get("sel_practice", None)
	check_get_more = request.REQUEST.get("check_get_more", None)
	if not recipient_id or not sel_practice:
		return HttpResponseRedirect('/')

	recipient_provider = None
	try:
		recipient_provider = Provider.objects.get(pk=recipient_id)
	except:
		return err403(request, err_msg=_("This recipient is not a Provider."))

	ret_data = {
			"goto_next_direct": True,
			"message": ""
		}

	show_get_more_page = False
	if check_get_more:
		mhluser = request.session['MHL_Users']['MHLUser']
		sender_id = mhluser.id
		show_get_more_page = check_show_get_more_provider(sender_id, 
				recipient_id, recipient_provider)
		if show_get_more_page:
			return HttpResponse(json.dumps(ret_data), mimetype='application/json')

	mgrs = list(Office_Manager.active_objects.filter(practice__pk=sel_practice))
	if REFER_FORWARD_CHOICES_ONLY_MANAGER == recipient_provider.user.refer_forward \
		and len(mgrs) > 0:
		managers = []
		for recipient in mgrs:
			managers.append(" ".join([
						recipient.user.user.first_name, 
						recipient.user.user.last_name
					]))
		receiver_role = "manager"
		if len(mgrs) > 1:
			receiver_role = "managers"
		ret_data["goto_next_direct"] = False
		ret_data["message"] = _("This referral will be sent to %(receiver_role)s:"
				" %(managers)s.<br/><br/>Do you wish to proceed?") % \
				({"receiver_role": receiver_role, "managers": ", ".join(managers)})

	return HttpResponse(json.dumps(ret_data), mimetype='application/json')


def check_show_get_more_provider(sender_id, recipient_id, recipient_provider):
	common_org_ids = get_common_org_ids(sender_id, recipient_id)
	if common_org_ids and len(common_org_ids) > 0:
		return False

	phys = list(Physician.objects.filter(user=recipient_provider))
	if len(phys) <= 0 or not phys[0].specialty:
		return False

	more_providers = get_more_providers(
			sender_id,
			phys[0].specialty)

	if not more_providers or len(more_providers) <= 0:
		return False
	return True


def save_refer(request, data, recipient_provider, context, file_list=None):
	sender = None
	if ('Provider' in request.session['MHL_Users']):
		sender = request.session['MHL_Users']['Provider']
	elif ('OfficeStaff' in request.session['MHL_Users']):
		sender = request.session['MHL_Users']['OfficeStaff']
	if sender is None:
		return err403(request)

	form = MessageReferForm(data)
	if form.is_valid():
		try:
			cur_prac = sender.current_practice
			user_recipients = data['user_recipients']
			context['user_recipients'] = user_recipients
			sel_practice = int(data['selected_practice'])
			mhluser = request.session['MHL_Users']['MHLUser']
			msg = Message(sender=request.user, subject=_('Refer'))
			msg.save()
			msg_body = msg.save_body(data['reason_of_refer'])

			forward_to_manager = True
			mgrs = list(Office_Manager.active_objects.filter(practice__pk=sel_practice))
			if REFER_FORWARD_CHOICES_ONLY_MANAGER == recipient_provider.user.refer_forward \
				and len(mgrs) > 0:
				forward_to_manager = False
				for recipient in mgrs:
					MessageRecipient(message=msg, user_id=recipient.user.user.id).save()
			else:
				MessageRecipient(message=msg, user_id=user_recipients).save()

			refer = form.save(commit=False)
			form.cleaned_data.update({
				'message': msg,
				'status': 'NO',
				'alternative_phone_number': ''
			})
			refer = encrypt_object(
				MessageRefer,
				form.cleaned_data,
				opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

			if file_list is None:
				file_list = get_file_list(request)
			attachments = generateAttachement(request, context, msg, file_list)
			msg.send(request, msg_body, attachment_objs=attachments,
					refer_objs=[refer])
			refer.refer_pdf = refer.uuid
			if cur_prac:
				refer.practice = cur_prac
			refer.save()

			data['today'] = datetime.date.today()
			context['refer_form'] = data
			try:
				rec = MHLUser.objects.get(pk=data['user_recipients'])
				context['user_recipient_name'] = get_fullname(rec)
			except:
				pass
			if cur_prac:
				context['current_practice_photo'] = ImageHelper.get_image_by_type(\
						cur_prac.practice_photo, size="Middle", type='Practice') 
				context['current_practice'] = cur_prac
			else:
				context['current_practice_photo'] = ""
				context['current_practice'] = ""

			context['referring_physician_name'] = get_fullname(mhluser)
			context['physician_phone_number'] = ''
			if mhluser and mhluser.mobile_phone:
				context['physician_phone_number'] = mhluser.mobile_phone
			generate_pdf(refer, request, context)
			send_refer_forward(refer, request, data,
					mgrs=mgrs, forward_to_manager=forward_to_manager)
			request.session[REFER_CACHE_SESSION_KEY] = None
			request.session[PREVENT_REPEAT_COMMIT_TOKEN] = None
		except KeyInvalidException:
			context["err_message"] = _("Sorry. Security Key Error. Please contact "
									"system administrator.")
		return render_to_response('DoctorCom/Messaging/refer_success.html', context)


def send_refer_forward(refer, request, data, mgrs=None, forward_to_manager=True):
	pdf_data = refer.decrypt_file(request)
	from MHLogin.DoctorCom.Messaging.views import getFormatToAndCc
	recipients, ccs = getFormatToAndCc(data['user_to_recipients'], 
						data['user_cc_recipients'])

	if pdf_data and ((mgrs and forward_to_manager) or recipients):
		msg = Message(
			sender=request.user,
			subject=u'Refer Forwarding',
			thread_uuid=uuid.uuid4().hex
		)
		msg.save()
		refer_msg_body = _("%s has forwarded you a referral, please see details in "
				"attachment.\n\nBest,\nDoctorCom\n") % \
				' '.join([request.user.first_name, request.user.last_name])
		msg_body = msg.save_body(refer_msg_body)
		user_ids_sent = []
		if mgrs and forward_to_manager:
			for recipient in mgrs:
				user_ids_sent.append(int(recipient.user.user.id))
		for recipient in recipients:
			user_ids_sent.append(recipient)
		user_ids_sent = list(set(user_ids_sent))

		if not user_ids_sent:
			return

		for recipient in user_ids_sent:
			MessageRecipient(message=msg, user_id=recipient).save()

		attachment = encrypt_object(
			MessageAttachment,
			{
				'message': msg,
				'size': len(pdf_data),
				'encrypted': True,
			},
			opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

		refer_forwarding_name = _('Refer Forwarding') + '.pdf'
		attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
		attachment.encrypt_filename(request, refer_forwarding_name)
		attachment.encrypt_file(request, [pdf_data])
		attachment.suffix = 'pdf'
		(attachment.content_type, attachment.encoding) = \
				mimetypes.guess_type(refer_forwarding_name)
		attachment.save()
		msg.send(request, msg_body, [attachment])	


def refresh_practice_info(request):
	try:
		practice_id = request.REQUEST.get("practice_id", None)
		selected_practice = get_object_or_404(PracticeLocation, pk=practice_id)

		practice_membersDict = dict()
		practice_members = all_staff_members(selected_practice)
		practice_membersDict['users'] = set_practice_members_result(practice_members, request)
		ret_data = {}
		ret_data['practice_members'] = render_to_string('allStaffs2.html', practice_membersDict)
		return HttpResponse(json.dumps(ret_data), mimetype='application/json')
	except:
		return err500(request)


def get_recipient_info(request, recipient_provider, current_user_mobile, context,\
			recipient_pracs=None, selected_practice_id=None):
	"""
	GetRecipientInfo
	:param request: http request
	:type request: HttpRequest
	:param recipient_provider: Recipient info
	:type recipient_provider: Provider or int  
	:param current_user_mobile: current_user_mobile
	:type current_user_mobile: string
	:param context: RequestContext
	:type context: dict
	:param recipient_pracs: practice list of recipient
	:type recipient_pracs: list of PracticeLocation
	:param selected_practice_id: selected practice id
	:type selected_practice_id: int
	:returns: None
	"""
	if recipient_provider:
		if not isinstance(recipient_provider, Provider):
			recipient_provider = int(recipient_provider)
			recipient_provider = get_object_or_404(Provider, pk=recipient_provider)

		phys = Physician.objects.filter(user=recipient_provider)
		if phys:
			phy = phys[0]
			clinical_clerk = phy.user.clinical_clerk
			context['specialty'] = "" if clinical_clerk \
					else phy.get_specialty_display()
			context['title'] = "" if clinical_clerk else "Dr."

		context['practice_photo'] = get_prefer_logo(recipient_provider.user.id, 
				current_practice=recipient_provider.current_practice)
		context['user_photo'] = ImageHelper.get_image_by_type(recipient_provider.photo,
				 type='Provider')
		context['provider'] = recipient_provider
		context['fullname']=get_fullname(recipient_provider)
		if not recipient_pracs:
			recipient_pracs = recipient_provider.practices.filter(
				organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
		context['practices'] = recipient_pracs

		try:
			selected_practice = PracticeLocation.objects.get(\
					pk=selected_practice_id)
		except:
			selected_practice = recipient_pracs[0] if recipient_pracs else None
		if selected_practice:
			context['selected_practice_id'] = selected_practice.id
		else:
			context['selected_practice_id'] = ""

		context['call_available'] = bool(recipient_provider.user.mobile_phone) and \
				current_user_mobile and settings.CALL_ENABLE
		context['pager_available'] = bool(recipient_provider.pager) \
				and settings.CALL_ENABLE

		practice_membersDict = dict()
		practice_members = all_staff_members(selected_practice)
		practice_membersDict['users'] = set_practice_members_result(practice_members, request)
		context['practice_members'] = render_to_string('allStaffs2.html', practice_membersDict)


def get_refer_info(request, context):
	refer_data = request.REQUEST
	file_list = get_file_list(request)
	if request.method == "GET" and REFER_CACHE_SESSION_KEY in request.session\
		and request.session[REFER_CACHE_SESSION_KEY]:
		refer_data = request.session[REFER_CACHE_SESSION_KEY]
		if "file_list" in refer_data:
			file_list = refer_data["file_list"]
		user_recipients = request.REQUEST.get("user_recipients", None)
		if user_recipients:
			refer_data["user_recipients"] = user_recipients

	clinical_form = ReferClinicalForm(refer_data)
	demographics_form = ReferDemographicsForm(refer_data)
	insurance_form = ReferInsuranceForm(refer_data)
	context['clinical_form'] = clinical_form
	context['demographics_form'] = demographics_form
	context['insurance_form'] = insurance_form
	context['file_list'] = file_list
	context['MAX_UPLOAD_SIZE'] = settings.MAX_UPLOAD_SIZE
	return clinical_form, demographics_form, insurance_form


def get_file_list(request):
	file_saved_names = request.REQUEST.getlist('file_saved_name')
	file_display_names = request.REQUEST.getlist('file_display_name')
	file_charsets = request.REQUEST.getlist('file_charset')
	file_sizes = request.REQUEST.getlist('file_size')	
	file_len = len(file_saved_names)
	file_list = [{
			'file_saved_name':file_saved_names[i],
			'file_display_name':file_display_names[i],
			'file_charset':file_charsets[i],
			'file_size':file_sizes[i],
		} for i in range(file_len)]
	return file_list


def update_refer(request, refer_id):
	"""
	update_refer

	:param request: Recipient info
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param refer_id: The refferal's id
	:type refer_id: int
	:returns: django.http.HttpResponse -- the preview dialog in a response object 
	"""
	if (request.method == 'GET'):
		form = ReferEditForm(request.GET)
		if form.is_valid():
			success = updateRefer(request, form, refer_id)
			if not success:
				return HttpResponse()

	return HttpResponse()


def download_pdf(request, refer_id):
	"""
	download_pdf

	:param request: Request info
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param refer_id: referall id
	:type refer_id: int  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	"""
	refer = get_object_or_404(MessageRefer, uuid=refer_id)

	if (request.user != refer.message.sender and not
			(request.user in refer.message.recipients.all())):
		return err403(request, err_msg="You don't seem to be a valid recipient for this file.")

	try:
		response = refer.get_file(request)
		return response
	except Exception as e: 
		err_email_body = '\n'.join([
		('PDF file not exist!'),
		''.join(['Server: ', settings.SERVER_ADDRESS]),
		''.join(['Session: ', str(request.session.session_key)]),
		''.join(['Message: ', (u'PDF file not exist in media/refer/pdf')]),
		''.join(['Exception: ', str(e)]),
		''.join(['Exception data: ', str(e.args)]),
		])
		mail_admins(_('PDF folder not exist'), err_email_body)
		raise Exception(_('A seemingly invalid URL has been stored for Refer Pdf.'))


def generateAttachement(request, context, msg, file_list):
	"""
	generateAttachement

	:param request: Request info
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param context: the RequestContext
	:type context: dict  
	:param msg: the message
	:type msg: string
	:param file_list: list of file information
	:type file_list: list of 
		{
			'file_saved_name':file_saved_names[i],
			'file_display_name':file_display_names[i],
			'file_charset':file_charsets[i],
			'file_size':file_sizes[i],
		}
	:returns: attachments array
	"""
	if not file_list or not isinstance(file_list, list):
		return []

	attachments = []
	for f in file_list:
		if not ("file_saved_name" in f and "file_display_name" in f \
			and "file_charset" in f and "file_size" in f):
			continue
		file_saved_name = f["file_saved_name"]
		file_display_name = f["file_display_name"]
		file_size = f["file_size"]
		file_charset = f["file_charset"]
		try:
			decrypt_str = FileHelper.readTempFile(file_saved_name, 'rb', 
										get_user_key(request))
			attachment = encrypt_object(
				MessageAttachment,
				{
					'message': msg,
					'size': file_size,
					'encrypted': True,
				},
				opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

			attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
			suffix = suffix_re.search(file_display_name)
			if (suffix):
				attachment.suffix = suffix.group(1)[:255].lower()
				(attachment.content_type, attachment.encoding) = \
					mimetypes.guess_type(file_display_name)
				attachment.charset = file_charset
			else:
				m = magic.Magic(mime=True)
				attachment.content_type = m.from_buffer(decrypt_str)
				if(attachment.content_type == 'application/dicom'):
					attachment.suffix = "dcm"
					file_display_name += ".dcm"
				m = magic.Magic(mime_encoding=True)
				attachment.encoding = m.from_buffer(decrypt_str)

			attachment.encrypt_filename(request, file_display_name)
			attachment.encrypt_file(request, decrypt_str)

			attachment.save()
			if "dcm" == attachment.suffix:
				thread.start_new_thread(sendToDicomServer, (
					{"name": file_display_name, "token": attachment.uuid,
						"content": decrypt_str},))
			attachments.append(attachment)
			FileHelper.deleteTempFile(file_saved_name)
		except (IOError):
			transaction.rollback()
			context['ioerror'] = True
			context['MAX_UPLOAD_SIZE'] = settings.MAX_UPLOAD_SIZE
	return attachments 

	################ TODO: ?? ################
	file_saved_names = request.POST.getlist('file_saved_name')
	file_display_names = request.POST.getlist('file_display_name')
	file_charsets = request.POST.getlist('file_charset')
	file_sizes = request.POST.getlist('file_size')
	file_len = len(file_saved_names)
	attachments = []

	if (file_len <= 0):
		return attachments

	for i in range(file_len):
		file_saved_name = file_saved_names[i]
		file_display_name = file_display_names[i]
		try:
			decrypt_str = FileHelper.readTempFile(file_saved_name, 'rb', 
										get_user_key(request))
			attachment = encrypt_object(
				MessageAttachment,
				{
					'message': msg,
					'size': file_sizes[i],
					'encrypted': True,
				},
				opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

			attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
			suffix = suffix_re.search(file_display_name)
			if (suffix):
				attachment.suffix = suffix.group(1)[:255].lower()
				(attachment.content_type, attachment.encoding) = \
					mimetypes.guess_type(file_display_name)
				attachment.charset = file_charsets[i]
			else:
				m = magic.Magic(mime=True)
				attachment.content_type = m.from_buffer(decrypt_str)
				if(attachment.content_type == 'application/dicom'):
					attachment.suffix = "dcm"
					file_display_name += ".dcm"
				m = magic.Magic(mime_encoding=True)
				attachment.encoding = m.from_buffer(decrypt_str)

			attachment.encrypt_filename(request, file_display_name)
			attachment.encrypt_file(request, decrypt_str)

			attachment.save()
			if "dcm" == attachment.suffix:
				thread.start_new_thread(sendToDicomServer, (
					{"name": file_display_name, "token": attachment.uuid,
						"content": decrypt_str},))
			attachments.append(attachment)
			FileHelper.deleteTempFile(file_saved_name)
		except (IOError):
			transaction.rollback()
			context['ioerror'] = True
			context['MAX_UPLOAD_SIZE'] = settings.MAX_UPLOAD_SIZE
	return attachments 

