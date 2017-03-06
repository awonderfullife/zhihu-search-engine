#-*- coding:utf-8 -*-import cv2
import numpy as np
import sys, os, lucene, threading, time
from bs4 import BeautifulSoup
from java.io import File
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.core import SimpleAnalyzer
#from org.apache.lucene.analysis.standard import CJKAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
import urllib
import cv2

class img_seacher_quick:
	def __init__(self,img):
		self.result_list = self.get_useful_picture(img)

	def get_future_num_color(self,img):
		(R,G,B) = cv2.split(img)
		R_avg = np.mean(R)
		G_avg = np.mean(G)
		B_avg = np.mean(B)
		max_val = max(R_avg, G_avg, B_avg) + 1
		R_stv = int(R_avg/max_val*10)
		G_stv = int(G_avg/max_val*10)
		B_stv = int(B_avg/max_val*10)
		if R_avg >= G_avg and R_avg >= B_avg: return 1000 + R_stv*100 + G_stv*10 + B_stv
		if G_avg >= R_avg and G_avg >= B_avg: return 2000 + R_stv*100 + G_stv*10 + B_stv
		if B_avg >= G_avg and B_avg >= R_avg: return 3000 + R_stv*100 + G_stv*10 + B_stv

	def get_future_num_quick0(self, img):
		small_picture = cv2.resize(img, (30,30))
		average = np.mean(small_picture)
		normal_picture = np.where(small_picture>average, 1, 0)
		index = 0
		for i in range(30):
			for j in range(30):
				if normal_picture[i][j][0] == 1:
					index += i*30 + j
		return index

	def get_future_num_quick1(self, img):
		small_picture = cv2.resize(img, (30,30))
		average = np.mean(small_picture)
		normal_picture = np.where(small_picture>average, 1, 0)
		index = 0
		for i in range(30):
			for j in range(30):
				if normal_picture[i][j][1] == 1:
					index += i*30 + j
		return index

	def get_future_num_quick2(self, img):
		small_picture = cv2.resize(img, (30,30))
		average = np.mean(small_picture)
		normal_picture = np.where(small_picture>average, 1, 0)
		index = 0
		for i in range(30):
			for j in range(30):
				if normal_picture[i][j][2] == 1:
					index += i*30 + j
		return index

	def analyse(self , img_dir):
		k = img_dir.split('/')
		j = k[4].split('___')
		return j[0] , j[1]

	def get_useful_picture(self , img):
		orb = cv2.ORB()
		result_list = []
		bf = cv2.BFMatcher(cv2.NORM_L2)
		kpa, desa = orb.detectAndCompute(img, None)
		self.storDir_num = self.get_future_num_color(img)
		self.storDir_num0 = self.get_future_num_quick0(img)
		self.storDir_num1 = self.get_future_num_quick1(img)
		self.storDir_num2= self.get_future_num_quick2(img)
		StorDir = "static/"+"Picture/" + str(self.storDir_num)
		storDir_2 = StorDir + "/" + str(self.storDir_num0) + '_' + str(self.storDir_num1) + '_' + str(self.storDir_num2)
		for filename in os.listdir(storDir_2):
			try:
				stor = storDir_2 + "/" + str(filename)
				img1 = cv2.imread(stor)
				kpi, desi = orb.detectAndCompute(img1, None)
				if desi == None :
					pass
				else :
					matches = bf.knnMatch(desa, trainDescriptors=desi, k=2)
					sub_matchpointnum = 0
					for m, n in matches:
						if m.distance < 0.85*n.distance:
							sub_matchpointnum += 1
					if sub_matchpointnum > 20:
						uty , uid = self.analyse(stor)
						result = []
						stor_new = '/'+stor
						result.append(stor_new)
						result.append(uty)
						result.append(uid)
						result_list.append(result)
			except Exception as e:
				print("Failed in read picture:", e)
		return result_list


class img_seacher_range:
	"""docstring for img_seacher_range"""
	def __init__(self, img):
		self.result_list = self.get_useful_picture(img)

	def get_future_num_color(self, img):
		#small_picture = cv2.resize(img, (250,250))
		(R,G,B) = cv2.split(img)
		R_avg = np.mean(R)
		G_avg = np.mean(G)
		#B_avg = np.mean(B)
		New_R = np.where(R>R_avg, 1, 0)
		New_G = np.where(G>G_avg, 2, 0)
		#New_B = np.where(B>B_avg, 4, 0)
		IMG_FINGER = New_R + New_G# + New_B
		ONE_DIMENSION = []
		for item in IMG_FINGER:
			ONE_DIMENSION.extend(item)
		class_array = np.bincount(ONE_DIMENSION)
		item_num = sum(ONE_DIMENSION)
		index = ''
		for val in class_array:
			new_val = int((val*1.0/item_num)*40)
			index = index + str(new_val)
		return index

	def analyse(self , img_dir):
		k = img_dir.split('/')
		j = k[3].split('___')
		return j[0] , j[1]

	def get_useful_picture(self , img):
		orb = cv2.ORB()
		# sift = cv2.SIFT()
		# kp1, des1 = sift.detectAndCompute(img, None)
		result_list = []
		bf = cv2.BFMatcher(cv2.NORM_L2)
		kpa, desa = orb.detectAndCompute(img, None)
		self.storDir_num = self.get_future_num_color(img)
		StorDir = "static/"+"Picture_new/" + self.storDir_num
		if not os.path.exists(StorDir):
			return result_list
		for filename in os.listdir(StorDir):
			try:
				stor = StorDir + "/" + str(filename)
				img1 = cv2.imread(stor)
				kpi, desi = orb.detectAndCompute(img1, None)
				if desi == None :
					continue
				else :
					matches = bf.knnMatch(desa, desi, k=2)
					sub_matchpointnum = 0
					for m, n in matches:
						if m.distance < 0.82*n.distance:
							sub_matchpointnum += 1
					if sub_matchpointnum > 20:
						# kp2, des2 = sift.detectAndCompute(img1, None)
						# FLANN_INDEX_KDTREE = 0
						# index_params = dict(algorithm = FLANN_INDEX_KDTREE , tree = 5)
						# seacher_params = dict (checks = 50)
						# flann = cv2.FlannBasedMatcher(index_params , seacher_params)
						# matches1 = flann.knnMatch(des1 , des2 , k =2 )
						# sub_matchpointnum1 = 0
						# for m , n in matches1 :
						# 	if m.distance < 0.80*n.distance:
						# 		sub_matchpointnum1 += 1
						# if sub_matchpointnum1 > 20 :
						uty , uid = self.analyse(stor)
						result = []
						stor_new = '/'+stor
						result.append(stor_new)
						result.append(uty)
						result.append(uid)
						result_list.append(result)
			except Exception as e:
				print("Failed in read picture:", e)
		return result_list


class img_seacher_id:
	def __init__(self, id ):
		self.result_list = self.get_useful_picture(id)

	def get_useful_picture(self , id ):
		storDir = 'static/'+'Picture_user/' + str(id)
		result = []
		for filename in os.listdir(storDir):
			f = filename.spilt('_')
			if f[0] == str(0) or f[0] == str(1):
				stor = '/' + storDir + "/" + str(filename)
				result.append(stor)
		return stor




def use_seacher_range(img_storDir):
	img = cv2.imread(img_storDir)
	result = img_seacher_range(img).result_list
	return result


def use_seacher_quike(img_storDir):
	img = cv2.imread(img_storDir)
	result = img_seacher_quick(img).result_list
	return result


def use_seacher_id(img_storDir):
	img = cv2.imread('Pictures/' + str(img_storDir))
	result = img_seacher_id(img).result_list
	if len(result) == 0:
		result.append('static/dog.jpg')
	return result

