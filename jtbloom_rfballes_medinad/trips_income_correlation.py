import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from random import shuffle
from math import sqrt
import decimal


class trips_income_correlation(dml.Algorithm):
	contributor = 'jtbloom_rfballes_medinad'
	reads = ['jtbloom_rfballes_medinad.neighborhood_station_income_out']
	writes = ['jtbloom_rfballes_medinad.trips_income_correlation']


	def permute(x):
		shuffled = [xi for xi in x]
		shuffle(shuffled)
		return shuffled

	def avg(x): # Average
		return sum(x)/len(x)

	def stddev(x): # Standard deviation.
		m = trips_income_correlation.avg(x)
		return sqrt(sum([(xi-m)**2 for xi in x])/len(x))

	def cov(x, y): # Covariance.
		return sum([(xi-trips_income_correlation.avg(x))*(yi-trips_income_correlation.avg(y)) for (xi,yi) in zip(x,y)])/len(x)

	def corr(x, y): # Correlation coefficient.
		if trips_income_correlation.stddev(x)*trips_income_correlation.stddev(y) != 0:
			return trips_income_correlation.cov(x, y)/(trips_income_correlation.stddev(x)*trips_income_correlation.stddev(y))

	def p(x, y):
		c0 = trips_income_correlation.corr(x, y)
		corrs = []
		for k in range(0, 2000):
			y_permuted = trips_income_correlation.permute(y)
			corrs.append(trips_income_correlation.corr(x, y_permuted))
		return len([c for c in corrs if abs(c) > c0])/len(corrs)

	@staticmethod
	def execute(trial = False):

		'''Retrieve some data sets (not using the API here for the sake of simplicity).'''
		startTime = datetime.datetime.now()


    	# Set up the database connection.
		client = dml.pymongo.MongoClient()
		repo = client.repo
		repo.authenticate('jtbloom_rfballes_medinad', 'jtbloom_rfballes_medinad')

		repo.dropCollection('jtbloom_rfballes_medinad.trips_income_correlation')
		repo.createCollection('jtbloom_rfballes_medinad.trips_income_correlation')

		trips_inc = list(repo['jtbloom_rfballes_medinad.neighborhood_station_income_out'].find())

		income = []
		trips = []
		for item in trips_inc:
			inc = int(item['income'])
			income.append(inc)
			num_trips = int(item['trips'])
			trips.append(num_trips)

		pval = trips_income_correlation.p(income,trips)

		correl = trips_income_correlation.corr(income,trips)

		covarr = trips_income_correlation.cov(income,trips)

		stdevincome = trips_income_correlation.stddev(income)

		stdevtrips = trips_income_correlation.stddev(trips)

		avgincome = trips_income_correlation.avg(income)

		avgtrips = trips_income_correlation.avg(trips)


		print("pval = ", pval)
		print("correl = ", correl)
		print("covarr = ", covarr)
		print("stdev of income = ", stdevincome)
		print("stdev of trips = ", stdevtrips)
		print("avg income = ", avgincome)
		print("avg hubway = ", avgtrips)




	@staticmethod
	def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
		pass







trips_income_correlation.execute()