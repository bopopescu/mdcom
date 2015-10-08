'''
Created on 2012-04-24
Update on 2012-09-19
@author: htian
'''
from __future__ import division
from django.conf import settings
from PIL import Image
import os

DEFAULT_PICTURE = {
			'':'',
			'Practice':''.join([settings.MEDIA_URL, 'images/photos/hospital_icon.jpg']),
			'Provider':''.join([settings.MEDIA_URL, 'images/photos/avatar2.png']),
			'Staff':''.join([settings.MEDIA_URL, 'images/photos/staff_icon.jpg']),
			'Broker':''.join([settings.MEDIA_URL, 'images/photos/broker.jpg']),
			'Nurse':''.join([settings.MEDIA_URL, 'images/photos/nurse.jpg']),
		}

PICTURE_STYPE = {
				'img_size': (
					("Small", 60, 70),
					("Middle", 100, 130),
				),
				'img_size_practice': (
					("Small", 60, 18),
					("Middle", 100, 30),
					("Large", 400, 150),
				),
				'img_size_logo':(
					("Small", 80, 30),
					("Middle", 240, 90),
					("Large", 400, 150),
				)
#old size
#				'img_size_logo':(
#					("Small", 80, 30),
#					("Middle", 80, 35),
#					("Large", 80, 40),
#				)
			}

def get_full_url(url, media_url=settings.MEDIA_URL):
	return ''.join([settings.INSTALLATION_PATH, media_url, url])

def get_url_list(url, resize_type):
	url_list = []
	url_list.append(url)
	base, ext = os.path.splitext(url)
	for pic in PICTURE_STYPE.get(resize_type, []):
		url_list.append(''.join([base, '_', pic[0], ext]))
	return url_list

def delete_image(url, resize_type):
	if not url:
		return

	for image_url in get_url_list(url, resize_type):
		try:
			os.remove(get_full_url(image_url))
		except:
			pass

def generate_image(old_url, new_url, resize_type='img_size'):
	if(old_url == new_url or not new_url):
		return None
	delete_image(old_url, resize_type)

	image_path = get_full_url(new_url)
	base, ext = os.path.splitext(image_path)
	try:
		im = Image.open(image_path) 
	except IOError:
		return False

	for size in PICTURE_STYPE.get(resize_type, []):
		filename = ''.join([base, '_', size[0], ext])
		thumb = resize_image(im, size[1], size[2])
		thumb.save(filename, quality=100)
	return True

def get_image_by_type(image, size=None, type='Provider', resize_type='img_size'):

	default = DEFAULT_PICTURE.get(type, '')

	if not image or not image.name:
		return default

	try:
		photo_url = get_url_by_size(image.name, size)

		if os.path.exists(get_full_url(photo_url)):
			return settings.MEDIA_URL + photo_url
		elif os.path.exists(get_full_url(image.name)):
			generate_image(None, image.name, resize_type)
			return settings.MEDIA_URL + photo_url
		else:
			return default
	except:
		return default


def resize_image(im, x, y):
	(wx, wy) = im.size
	if wx <= x and wy <= y:
		return im

	rx = wx * 1.0 / x
	ry = wy * 1.0 / y

	if rx > ry:
		x = wx / rx
		y = wy / rx
	else:
		x = wx / ry
		y = wy / ry
		
	return im.resize((int(x), int(y)), Image.ANTIALIAS)

def get_url_by_size(url, size):
	if not size:
		return url
	base, ext = os.path.splitext(url)
	return ''.join([base, '_', size, ext])

#add by xlin 121226 to reset logo size
def get_image_width(image, size='Large', type='Provider'):
	try:
		logo_url = get_full_url(get_url_by_size(image.name, size))
	except:
		logo_url = get_full_url(image.name)
	
	if os.path.exists(logo_url):
		im = Image.open(logo_url)
	else:
		default = DEFAULT_PICTURE[type]
		logo_url = ''.join([settings.INSTALLATION_PATH, default])
		im = Image.open(logo_url)
		
	return reset_width(im.size[0], im.size[1])

def get_image_height(image, size='Large', type='Provider'):
	try:
		logo_url = get_full_url(get_url_by_size(image.name, size))
	except:
		logo_url = get_full_url(image.name)
	if os.path.exists(logo_url):
		im = Image.open(logo_url)
	else:
		default = DEFAULT_PICTURE[type]
		logo_url = ''.join([settings.INSTALLATION_PATH, default])
		im = Image.open(logo_url)
	return reset_height(im.size[0], im.size[1])

def reset_width(w, h):
	if w < 200 and h < 50:
		return w
	if w / h == 4:
		return 200
	if w / h > 4:
		return 200
	if w / h < 4:
		return 50 / h * w

def reset_height(w, h):
	if w < 200 and h < 50:
		return h
	if w / h == 4:
		return 50
	if w / h < 4:
		return 50
	if w / h > 4:
		return 200 / w * h
