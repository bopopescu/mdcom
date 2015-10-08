#-*- coding: utf-8 -*-
from django.test import TestCase
from django.conf import settings
from MHLogin.utils.ImageHelper import get_full_url, get_url_list, \
	generate_image, delete_image, get_image_by_type
import os
import mock
from MHLogin.utils import ImageHelper

class ImageObject(object):
	name = None

class ImageHelperTest(TestCase):
	@classmethod
	def setUpClass(cls): 
		clean_test_image()

	@classmethod
	def tearDownClass(cls):
		clean_test_image()

	def test_get_full_url(self):
		data=[{
				'url':"images\abc.jpg", 'media_url': settings.MEDIA_URL,
				'result': ''.join([settings.INSTALLATION_PATH, settings.MEDIA_URL, "images\abc.jpg"])
			}]
		for d in data:
			self.assertEqual(get_full_url(d['url']), d['result'])

	def test_get_url_list(self):
		data=[{'url':"/images/test.jpg", 'resize_type':'img',
			'result': ["/images/test.jpg"]},
			{'url':"/images/test.jpg", 'resize_type':'img_size',
			'result': ["/images/test.jpg", "/images/test_Small.jpg", "/images/test_Middle.jpg"]},
			{'url':"/images/test.jpg", 'resize_type':'img_size_logo',
			'result': ["/images/test.jpg", "/images/test_Small.jpg", "/images/test_Middle.jpg", "/images/test_Large.jpg"]},
			{'url':"/images/test.jpg", 'resize_type':'img_size_practice',
			'result': ["/images/test.jpg", "/images/test_Small.jpg", "/images/test_Middle.jpg", "/images/test_Large.jpg"]},
		]
		for d in data:
			self.assertListEqual(get_url_list(d['url'], d['resize_type']), d['result'])

	def test_generate_image(self):
		test_img_path = "images/photos/test/test.png"
		data=[
			{'oldurl':"images/test.jpg", 'newurl':'images/test.jpg',
			'has_called':False, 'result': None},
			{'oldurl':"images/test.jpg", 'newurl':'',
			'has_called':False, 'result': None},
			{'oldurl':"images/test.jpg", 'newurl':'images/test2.jpg',
			'has_called':False, 'result': False},
			{'oldurl':"", 'newurl':test_img_path,
			'has_called':True, 'result': True},
		]

		for d in data:
			self.assertEqual(generate_image(d['oldurl'], d['newurl']), d['result'])
			if d['has_called']:
				pass
		for img in get_url_list(test_img_path, 'img_size'):
			if img != test_img_path:
				delete_image(img, 'img_size')

	def test_delete_image(self):
		test_img_path = "images/photos/test/test.png"
		generate_image('', test_img_path)
		for img in get_url_list(test_img_path, 'img_size'):
			if img != test_img_path:
				self.assertTrue(os.path.exists(get_full_url(img)))
				delete_image(img, 'img_size')
				self.assertFalse(os.path.exists(get_full_url(img)))

	def test_get_image_by_type(self):
		test_img_path = "images/photos/test/test.png"
		test_img = ImageObject()
		test_img.name = test_img_path
		data=[
			{'image': None, 'size':'', 'result': "/media/images/photos/avatar2.png"},
			{'image': ImageObject(), 'size':'Small', 'result': "/media/images/photos/avatar2.png"},
			{'image': test_img, 'size': None, 'result': "/media/images/photos/test/test.png"},
			{'image': test_img, 'size': 'Small', 'called': True, 'result': "/media/images/photos/test/test_Small.png"},
			{'image': test_img, 'size': 'Small', 'called': False, 'result': "/media/images/photos/test/test_Small.png"},
			
		]
		for d in data:
			if 'called' in d:
				with mock.patch.object(ImageHelper, 'generate_image') as mymock:
					get_image_by_type(d['image'], d['size'])
					self.assertEqual(mymock.called, d['called'])
			self.assertEqual(get_image_by_type(d['image'], d['size']), d['result'])


def clean_test_image():
	test_img_path = 'images/photos/test/test.png'
	for img in get_url_list(test_img_path, 'img_size'):
		if img != test_img_path:
			delete_image(img, 'img_size')



