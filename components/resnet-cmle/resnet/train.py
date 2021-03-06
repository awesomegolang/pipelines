# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import base64, sys, json
import tensorflow as tf
import argparse
import json
import os
from time import gmtime, strftime
import subprocess
import logging

logging.getLogger().setLevel(logging.INFO)

def parse_arguments():
  """Parse command line arguments."""
  parser = argparse.ArgumentParser()
  parser.add_argument('--data_dir',
                      type = str,
                      default = 'gs://flowers_resnet/tpu/resnet/data',
                      help = 'The data directory file generated by the preprocess component.')
  parser.add_argument('--output',
                      type = str,
                      help = 'Path to GCS location to store output.')
  parser.add_argument('--region',
                      type = str,
                      default = 'us-central1',
                      help = 'Region to use.')
  parser.add_argument('--depth',
                      type = int,
                      default = 50,
                      help = 'Depth of ResNet model.')
  parser.add_argument('--train_batch_size',
                      type = int,
                      default = 128,
                      help = 'Batch size for training.')
  parser.add_argument('--eval_batch_size',
                      type = int,
                      default = 32,
                      help = 'Batch size for validation.')
  parser.add_argument('--steps_per_eval',
                      type = int,
                      default = 250,
                      help = 'Steps per evaluation.')
  parser.add_argument('--train_steps',
                      type = int,
                      default = 10000,
                      help = 'Number of training steps.')
  parser.add_argument('--num_train_images',
                      type = int,
                      default = 3300,
                      help = 'Number of training set images.')
  parser.add_argument('--num_eval_images',
                      type = int,
                      default = 370,
                      help = 'Number of validation set images.')
  parser.add_argument('--num_label_classes',
                      type = int,
                      default = 5,
                      help = 'Number of classes.')
  parser.add_argument('--TFVERSION',
                      type = str,
                      default = '1.9',
                      help = 'Version of TensorFlow to use.')
  args = parser.parse_args()
  return args


if __name__== "__main__":
  args = parse_arguments()
  job_name = 'imgclass_' + strftime("%y%m%d_%H%M%S", gmtime())

  output_dir = args.output + '/tpu/model'
  logging.info('Submitting job for training to Cloud Machine Learning Engine')
  subprocess.check_call('gcloud ml-engine jobs submit training ' + job_name + ' \
  --region=' + args.region + ' \
  --module-name=trainer.resnet_main \
  --package-path=/resnet/resnet_model/trainer \
  --job-dir=' + output_dir + ' \
  --scale-tier=BASIC_TPU \
  --stream-logs \
  --runtime-version=' + args.TFVERSION + ' \
  -- \
  --data_dir=' + args.data_dir + ' \
  --model_dir=' + output_dir + ' \
  --use_tpu=True \
  --resnet_depth=' + str(args.depth) + ' \
  --train_batch_size=' + str(args.train_batch_size) + ' --eval_batch_size=' + str(args.eval_batch_size) + ' --skip_host_call=True \
  --steps_per_eval=' + str(args.steps_per_eval) + ' --train_steps=' + str(args.train_steps) + ' \
  --num_train_images=' + str(args.num_train_images) + '  --num_eval_images=' + str(args.num_eval_images) + '  --num_label_classes=' + str(args.num_label_classes) + ' \
  --export_dir=' + output_dir + '/export', shell=True)

  with open("/output.txt", "w") as output_file:
    output_file.write(output_dir)

  metadata = {
    'outputs' : [{
      'type': 'tensorboard',
      'source': output_dir,
    }]
  }
  with open('/mlpipeline-ui-metadata.json', 'w') as f:
    json.dump(metadata, f)
