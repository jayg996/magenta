# Copyright 2019 The Magenta Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for performance_rnn_pipeline."""

from magenta.models.performance_rnn import performance_rnn_pipeline
from magenta.music import sequences_lib
from magenta.music import testing_lib as music_testing_lib
from magenta.protobuf import music_pb2

import tensorflow as tf

FLAGS = tf.app.flags.FLAGS


class PerformanceRnnPipelineTest(tf.test.TestCase):

  def setUp(self):
    self.note_sequence = music_pb2.NoteSequence()
    self.note_sequence.ticks_per_quarter = 220

  def testExtractPerformances(self):
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 0, [(60, 100, 0.0, 4.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence_absolute(
        self.note_sequence, steps_per_second=100)

    perfs, _ = performance_rnn_pipeline.extract_performances(quantized_sequence)
    self.assertEqual(1, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=1, max_events_truncate=10)
    self.assertEqual(1, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=8, max_events_truncate=10)
    self.assertEqual(0, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=1, max_events_truncate=3)
    self.assertEqual(1, len(perfs))
    self.assertEqual(3, len(perfs[0]))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, max_steps_truncate=100)
    self.assertEqual(1, len(perfs))
    self.assertEqual(100, perfs[0].num_steps)

  def testExtractPerformancesMultiProgram(self):
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(60, 100, 0.0, 4.0), (64, 100, 0.0, 3.0), (67, 100, 1.0, 2.0)])
    self.note_sequence.notes[0].program = 2
    quantized_sequence = sequences_lib.quantize_note_sequence_absolute(
        self.note_sequence, steps_per_second=100)

    perfs, _ = performance_rnn_pipeline.extract_performances(quantized_sequence)
    self.assertEqual(0, len(perfs))

  def testExtractPerformancesNonZeroStart(self):
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 0, [(60, 100, 0.0, 4.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence_absolute(
        self.note_sequence, steps_per_second=100)

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, start_step=400, min_events_discard=1)
    self.assertEqual(0, len(perfs))
    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, start_step=0, min_events_discard=1)
    self.assertEqual(1, len(perfs))

  def testExtractPerformancesRelativeQuantized(self):
    self.note_sequence.tempos.add(qpm=60.0)
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 0, [(60, 100, 0.0, 4.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, steps_per_quarter=100)

    perfs, _ = performance_rnn_pipeline.extract_performances \
        (quantized_sequence)
    self.assertEqual(1, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=1, max_events_truncate=10)
    self.assertEqual(1, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=8, max_events_truncate=10)
    self.assertEqual(0, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=1, max_events_truncate=3)
    self.assertEqual(1, len(perfs))
    self.assertEqual(3, len(perfs[0]))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, max_steps_truncate=100)
    self.assertEqual(1, len(perfs))
    self.assertEqual(100, perfs[0].num_steps)

  def testExtractPerformancesSplitInstruments(self):
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 0, [(60, 100, 0.0, 4.0)])
    music_testing_lib.add_track_to_sequence(
        self.note_sequence, 1, [(62, 100, 0.0, 2.0), (64, 100, 2.0, 4.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence_absolute(
        self.note_sequence, steps_per_second=100)

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, split_instruments=True)
    self.assertEqual(2, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=8, split_instruments=True)
    self.assertEqual(1, len(perfs))

    perfs, _ = performance_rnn_pipeline.extract_performances(
        quantized_sequence, min_events_discard=16, split_instruments=True)
    self.assertEqual(0, len(perfs))


if __name__ == '__main__':
  tf.test.main()
