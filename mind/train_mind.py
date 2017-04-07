#!/usr/local/bin/python3

"""This module demonstrates the scoring model
behind Prophet

Created on Jan 09, 2017
@author: Matthew Sevrens
"""

#################### USAGE ##########################

# python3 -m mind.train_mind config/mind_model_config.json
# python3 -m mind.train_mind [config_file]

# http://www.metaculus.com/help/scoring
# https://arxiv.org/pdf/1610.10099.pdf
# https://github.com/paarthneekhara/byteNet-tensorflow/

#####################################################

import logging
import math
import sys

import numpy as np

from mind.mind_models import TruthModel
from mind.tools import load_dict_list, load_json, load_piped_dataframe

# Utility
logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument(
	'--resume_model', 
	type=str, 
	default=None, 
	help='Pre-trained model path, to resume from'
)

def load_data(config):
	"""Load training data"""

	dataset = config["dataset"]
	df = load_piped_dataframe(dataset, chunksize=256)

	msk = np.random.rand(len(df)) < 0.90
	train = df[msk]
	test = df[~msk]

	return train, test

def train_predictor(config):
	"""Train a language model via prediction"""

	epochs = config["options"]["max_epochs"]
	model_options = config["predictor"]
	lr = config["options"]["learning_rate"]
	beta1 = config["options"]["adam_momentum"]
	model = MindModel(model_options)
	tensors = model.build_prediction_model()

	optim = tf.train.AdamOptimizer(lr, beta1=beta1).minimize(tensors["loss"], var_list=tensors["variables"])

	sess = tf.InteractiveSession()
	tf.initialize_all_variables().run()
	saver = tf.train.Saver()

	if config.resume_model:
		saver.restore(sess, config["resume_model"])

	for i in range(epochs):
		print("Epoch: " + str(i))

def train_translator(config):
	"""Train a translator"""

def train_prophet(config):
	"""Train a truth model"""

def main():
	"""Run module from command line"""

	args = parser.parse_args()
	config = load_json(sys.argv[1])
	config["resume_model"] = args.resume_model
	model_type = config.options.model_type

	if model_type == "predictor":
		print("predictor")
	elif model_type == "translator":
		print("translator")
	elif model_type == "prophet":
		print("prophet")

if __name__ == "__main__":

	main()

	# scores = load_dict_list("data/input/ubs_votingapi_vote.csv")
	# truth_scores = [x for x in scores if x["tag"] == "Prescience"]

	# TODO
	# Load associated thoughts and merge data

	# print(len(truth_scores))

	#for score in truth_scores:
	#	print(score)

	# TODO
	# Temporal CNN for encoding thoughts using diluted convolutions
	# Append output of cnn to encodings of [time of day]:
	# 
	# df['sin_time'] = np.sin(2*np.pi*df.seconds/seconds_in_day)
	# df['cos_time'] = np.cos(2*np.pi*df.seconds/seconds_in_day)
	#
	# [day_of_year]
	#
	# [truth (0, 1)]
	#
	# [dissonance]
	#
	# [temporal_focus {-1, 0, 1}] 
	#
	# [sentiment (-1, 1)]
	#
	# [speaker]
	# Speaker embedding 

	# TODO
	# Take concatenated feautures and feed thoughts sequentially into an LSTM
	# Use the output state at each step as an input to a decoder
	# Attempt to reconctruct the input thoughts, and to generate subsequent thoughts
	# yet to be fed into the network
	# 
	# The intial loss is just the reconstruction of present, past and future thoughts
	# Some thoughts may have words modified via a thesaurus for the reconstruction signal
	#
	# After output sounds somewhat logical the loss will switch to dissonance fedback from the crowd
	# on thoughts generated
	# 
	# Perhaps a dual loss of truth and dissonance can be used. Maximize truth and minimize dissonance simultaneously

	# TODO
	# Analytics
	# How many thoughts have more than one truth vote?
	# How many unique users have logged votes?
	# How many thoughts have dissonance between users?
	# What is the distribution of truth votes?

	# Should reward more: correct contrarianism
	# Should reward less: correct alignment with the crowd
	# Should penalize more: incorrect contrarianism
	# Should penalize less: incorrect alignment with the crowd

	# One vote per day