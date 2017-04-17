#!/usr/local/bin/python3

"""This module demonstrates the scoring model
behind Prophet

Created on Jan 09, 2017
@author: Matthew Sevrens
"""

#################### USAGE ##########################

# python3 -m mind.train_mind config/mind_config.json
# python3 -m mind.train_mind [config_file]

# http://www.metaculus.com/help/scoring
# https://arxiv.org/pdf/1610.10099.pdf
# https://github.com/paarthneekhara/byteNet-tensorflow/

#####################################################

import logging
import math
import sys
import argparse

import numpy as np
import tensorflow as tf

from mind.mind_models import TruthModel
from mind.data_loaders import PretrainData
from mind.tools import load_dict_list, load_json, load_piped_dataframe

# Utility
logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("config", nargs="*")
parser.add_argument(
	'--resume_model', 
	type=str, 
	default=None, 
	help='Pre-trained model path, to resume from'
)

def pretrain_prophet(config):
	"""Train a language model via sequential thought prediction"""

	epochs = config["options"]["max_epochs"]

	# Load Data
	thought_stream = PretrainData(config["options"]["bucket_quant"], config)
	buckets, source_vocab, target_vocab, frequent_keys = thought_stream.bucket_data()

	# Configure Model Options
	model_options = config["prophet"]
	model_options["n_source_quant"] = len(source_vocab)
	model_options["n_target_quant"] = len(target_vocab)
	model_options["source_mask_chars"] = [source_vocab["padding"]]
	model_options["target_mask_chars"] = [target_vocab["padding"]]

	last_saved_model_path = None

	if "resume_model" in config:
		last_saved_model_path = config["resume_model"]

	# Train Model
	for i in range(1, epochs):

		cnt = 0

		key = model_options["sample_size"]
		cnt += 1
		
		print(("Key", cnt, key))

		sess = tf.InteractiveSession()

		step = 0
		batch_size = model_options["batch_size"]

		# Build Model
		model = TruthModel(model_options)
		tensors = model.build_truth_model(sample_size=key)
		
		# Build Optimizer
		lr = config["options"]["learning_rate"]
		beta1 = config["options"]["adam_momentum"]
		adam = tf.train.AdamOptimizer(lr, beta1=beta1)

		# Gradient Clipping
		optim = adam.minimize(tensors["loss"], var_list=tensors["variables"])

		# Initialize Variables and Summary Writer
		train_writer = tf.summary.FileWriter('logs/', sess.graph)
		tf.global_variables_initializer().run()

		saver = tf.train.Saver()

		# Restore previous checkpoint if existing
		if last_saved_model_path:
			print("Restoring Model")
			saver.restore(sess, last_saved_model_path)

		# Training Step
		while (step + 1) < len(buckets[key]):

			source, target = thought_stream.load_batch(step, buckets)
			kl_weight = (step / len(buckets[key]))
			kl_weight = 1 if i > 1 else kl_weight
			print("KL Weight: " + str(kl_weight))

			tensors_to_get = [
				optim, 
				tensors['loss'], 
				tensors['prediction'], 
				tensors['merged_summary'],
				tensors['kl_loss']
			]

			feed_dict = {
				"source_sentence:0" : source,
				"target_sentence:0" : target,
				"kl_weight:0" : kl_weight,
				"phase:0" : 1
			}

			# Run Session and Expand Outputs
			outputs = sess.run(tensors_to_get, feed_dict=feed_dict)
			_, loss, prediction, summary, kl_loss = outputs

			# Write to Summary
			train_writer.add_summary(summary, step)

			print("\n")

			print(("Loss", loss, kl_loss, step, len(buckets[key]), i, cnt, key))
			
			# Print Results to Terminal
			print("******")
			print(("Source ", thought_stream.char_indices_to_string(source[len(source) - 1], source_vocab)))
			print("---------")
			print(("Target ", thought_stream.word_indices_to_string(target[0], target_vocab)))
			print("----------")
			print(("Prediction ", thought_stream.word_indices_to_string(prediction[0:int(key)], target_vocab)))
			print("******")

			step += 1

			if step > 0 and step % 500 == 0:
				feed_dict["phase:0"] = 0
				new_thought = sess.run(tensors['prediction'], feed_dict=feed_dict)
				print("----------")
				print(("Generated Thought: ", thought_stream.word_indices_to_string(new_thought[0:int(key)], target_vocab)))
				print("******")

			if step % 5000 == 0:
				print("Saving Model")
				save_path = saver.save(sess, "models/model_pretrain_epoch_{}_{}.ckpt".format(i, cnt))
				last_saved_model_path = "models/model_pretrain_epoch_{}_{}.ckpt".format(i, cnt)

		# Save Checkpoint
		save_path = saver.save(sess, "models/model_pretrain_epoch_{}.ckpt".format(i))
		last_saved_model_path = "models/model_pretrain_epoch_{}.ckpt".format(i)

		tf.reset_default_graph()
		sess.close()

def train_prophet(config):
	"""Train a truth model"""

	epochs = config["options"]["max_epochs"]
	model_options = config["prophet"]

def main():
	"""Run module from command line"""

	args = parser.parse_args()
	config = load_json(args.config[0])
	model_type = config["options"]["model_type"]

	if args.resume_model:
		config["resume_model"] = args.resume_model

	if model_type == "predictor":
		pretrain_prophet(config)
	elif model_type == "prophet":
		train_prophet(config)

if __name__ == "__main__":
	main()