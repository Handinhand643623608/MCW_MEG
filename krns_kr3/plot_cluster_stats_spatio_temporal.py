# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 12:01:53 2014
=================================================================
Permutation t-test on source data with spatio-temporal clustering
=================================================================

Tests if the evoked response is significantly different between
conditions across subjects (simulated here using one subject's data).
The multiple comparisons problem is addressed with a cluster-level
permutation test across space and time.

"""

# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Eric Larson <larson.eric.d@gmail.com>
# License: BSD (3-clause)

print(__doc__)

import os.path as op
import numpy as np
from numpy.random import randn
from scipy import stats as stats
import matplotlib.pylab as plt

import mne
from mne import (io, spatial_tris_connectivity, compute_morph_matrix,
                 grade_to_tris)
from mne.epochs import equalize_epoch_counts
from mne.stats import (spatio_temporal_cluster_1samp_test,
                       summarize_clusters_stc)
from mne.minimum_norm import apply_inverse, read_inverse_operator
from mne.datasets import sample
from mne.viz import mne_analyze_colormap

import surfer
from surfer.viz import Brain
from surfer import Brain


###############################################################################
# Set parameters
data_path = '/home/custine/MEG/data/krns_kr3/9367/s5/'
#raw_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw.fif'
#event_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw-eve.fif'
subjects_dir = '/mnt/file1/binder/KRNS/anatomies/surfaces/'

tmin = -0.2
tmax = 0.3  # Use a lower tmax to reduce multiple comparisons
gradRej = 2000e-13
magRej = 3000e-15
magFlat = 1e-14
gradFlat = 1000e-15

#   Setup for reading the raw data
#raw = io.Raw(raw_fname)
#events = mne.read_events(event_fname)

###############################################################################
## Read epochs for all channels, removing a bad one
#raw.info['bads'] += ['MEG 2443']
#picks = mne.pick_types(raw.info, meg=True, eog=True, exclude='bads')
#event_id = 1  
#reject = dict(grad=2000e-13, mag=3000e-15)
#epochs1 = mne.Epochs(raw, events, event_id, tmin, tmax, picks=picks,
#                     baseline=(None, 0), reject=reject, preload=True)
#
#event_id = 3  # L visual
#epochs2 = mne.Epochs(raw, events, event_id, tmin, tmax, picks=picks,
#                     baseline=(None, 0), reject=reject, preload=True)
#
##    Equalize trial counts to eliminate bias (which would otherwise be
##    introduced by the abs() performed below)
#equalize_epoch_counts([epochs1, epochs2])

###############################################################################
# Transform to source space

fname_inv = data_path + 'ave_projon/9367_s5_Noun_People_All-ave-7-meg-inv.fif'
evoked1_fname = data_path + 'ave_projon/9367_s5_Noun_People_All-ave.fif'
evoked2_fname = data_path + 'ave_projon/9367_s5_Noun_Place_All-ave.fif'

snr = 3.0
lambda2 = 1.0 / snr ** 2
method = "dSPM"  # use dSPM method (could also be MNE or sLORETA)
inverse_operator = read_inverse_operator(fname_inv)
sample_vertices = [s['vertno'] for s in inverse_operator['src']]

#    Let's average and compute inverse, resampling to speed things up
#evoked1 = epochs1.average()
evoked1 = mne.read_evokeds(evoked1_fname, condition = 'epochs_TaggedWord')
print evoked1
print 
print inverse_operator
#evoked1.resample(50)
condition1 = apply_inverse(evoked1, inverse_operator, lambda2, method)

#evoked2 = epochs2.average()
evoked2 = mne.read_evokeds(evoked2_fname, condition = 'epochs_TaggedWord')
print evoked1
print 
print inverse_operator
#evoked2.resample(50)
condition2 = apply_inverse(evoked2, inverse_operator, lambda2, method)

#    Let's only deal with t > 0, cropping to reduce multiple comparisons
condition1.crop(0, None)
condition2.crop(0, None)
tmin = condition1.tmin
tstep = condition1.tstep
#
print np.shape(condition2.data)
#########################################################################################################################################################################################################33##############################################################################################################################3
# Transform to common cortical space

#    Normally you would read in estimates across several subjects and morph
#    them to the same cortical space (e.g. fsaverage). For example purposes,
#    we will simulate this by just having each "subject" have the same
#    response (just noisy in source space) here. Note that for 7 subjects
#    with a two-sided statistical test, the minimum significance under a
#    permutation test is only p = 1/(2 ** 6) = 0.015, which is large.
n_vertices_sample, n_times = condition1.data.shape
n_subjects = 2
print('Simulating data for %d subjects.' % n_subjects)

#    Let's make sure our results replicate, so set the seed.
np.random.seed(0)
X = randn(n_vertices_sample, n_times, n_subjects, 2) * 10
print X.shape 
print np.newaxis
X[:, :, :, 0] += condition1.data[:, :, np.newaxis]
X[:, :, :, 1] += condition2.data[:, :, np.newaxis]

#    It's a good idea to spatially smooth the data, and for visualization
#    purposes, let's morph these to fsaverage, which is a grade 5 source space
#    with vertices 0:10242 for each hemisphere. Usually you'd have to morph
#    each subject's data separately (and you might want to use morph_data
#    instead), but here since all estimates are on 'sample' we can use one
#    morph matrix for all the heavy lifting.
fsave_vertices = [np.arange(10242), np.arange(10242)]
morph_mat = compute_morph_matrix('9367', 'fsaverage', sample_vertices,
                                 fsave_vertices, 20, subjects_dir)
print morph_mat.shape
print "Jane Here Here Here Here"                                  
n_vertices_fsave = morph_mat.shape[0]

#    We have to change the shape for the dot() to work properly
X = X.reshape(n_vertices_sample, n_times * n_subjects * 2)

print np.shape(X)
print('Morphing data.')
X = morph_mat.dot(X)  # morph_mat is a sparse matrix
X = X.reshape(n_vertices_fsave, n_times, n_subjects, 2)
print np.shape(X)

#    Finally, we want to compare the overall activity levels in each condition,
#    the diff is taken along the last axis (condition). The negative sign makes
#    it so condition1 > condition2 shows up as "red blobs" (instead of blue).
X = np.abs(X)  # only magnitude
X = X[:, :, :, 0] - X[:, :, :, 1]  # make paired contrast *********************COND 1 - RED********************
print "Overall activity - difference in activity across conditions.."
print np.shape(X)

###############################################################################
# Compute statistic

#    To use an algorithm optimized for spatio-temporal clustering, we
#    just pass the spatial connectivity matrix (instead of spatio-temporal)
print('Computing connectivity.')
connectivity = spatial_tris_connectivity(grade_to_tris(5))

#    Note that X needs to be a multi-dimensional array of shape
#    samples (subjects) x time x space, so we permute dimensions
X = np.transpose(X, [2, 1, 0])
print np.shape(X)


##########################################################################################################################33
##############################################################################################################################3

#    Now let's actually do the clustering. This can take a long time...
#    Here we set the threshold quite high to reduce computation.
p_threshold = 0.01 #0.001
t_threshold = -stats.distributions.t.ppf(p_threshold / 2., n_subjects - 1)
print('Clustering.')
print t_threshold
print np.shape(X)
T_obs, clusters, cluster_p_values, H0 = clu = \
    spatio_temporal_cluster_1samp_test(X, connectivity=connectivity, n_jobs=2, threshold = t_threshold) 
                                       
print cluster_p_values                                           
#    Now select the clusters that are sig. at p < 0.05 (note that this value
#    is multiple-comparisons corrected).
good_cluster_inds = np.where(cluster_p_values < 0.1)[0]


################################################################################
# Visualize the clusters

print('Visualizing clusters.')
import os
os.environ["SUBJECTS_DIR"] = "/mnt/file1/binder/KRNS/anatomies/surfaces/"
os.environ["subjects_dir"] = "/mnt/file1/binder/KRNS/anatomies/surfaces/"

#    Now let's build a convenient representation of each cluster, where each
#    cluster becomes a "time point" in the SourceEstimate
stc_all_cluster_vis = summarize_clusters_stc(clu, tstep=tstep,
                                             vertno=fsave_vertices,
                                             subject='fsaverage')

#    Let's actually plot the first "time point" in the SourceEstimate, which
#    shows all the clusters, weighted by duration
colormap = mne_analyze_colormap(limits=[0, 10, 50])
#subjects_dir = op.join(data_path, 'subjects')
# blue blobs are for condition A < condition B, red for A > B
brain = stc_all_cluster_vis.plot('fsaverage', 'inflated', 'lh', colormap,
                                 time_label='Duration significant (ms)', time_viewer = True)
brain.set_data_time_index(0)
# The colormap requires brain data to be scaled -fmax -> fmax
brain.scale_data_colormap(fmin=-50, fmid=0, fmax=50, transparent=False)
brain.show_view('lateral')
brain.save_image('clusters.png')

##########################################################################################################################33
##########################################################################################################################33
##############################################################################################################################3
##############################################################################################################################3
## Transform to common cortical space
#
##    Normally you would read in estimates across several subjects and morph
##    them to the same cortical space (e.g. fsaverage). For example purposes,
##    we will simulate this by just having each "subject" have the same
##    response (just noisy in source space) here. Note that for 7 subjects
##    with a two-sided statistical test, the minimum significance under a
##    permutation test is only p = 1/(2 ** 6) = 0.015, which is large.
#n_vertices_sample, n_times = condition1.data.shape
#n_subjects = 7
#print('Simulating data for %d subjects.' % n_subjects)
#
##    Let's make sure our results replicate, so set the seed.
#np.random.seed(0)
#X = randn(n_vertices_sample, n_times, n_subjects, 2) * 10
#print X.shape 
#print np.newaxis
#X[:, :, :, 0] += condition1.data[:, :, np.newaxis]
#X[:, :, :, 1] += condition2.data[:, :, np.newaxis]
#
##    It's a good idea to spatially smooth the data, and for visualization
##    purposes, let's morph these to fsaverage, which is a grade 5 source space
##    with vertices 0:10242 for each hemisphere. Usually you'd have to morph
##    each subject's data separately (and you might want to use morph_data
##    instead), but here since all estimates are on 'sample' we can use one
##    morph matrix for all the heavy lifting.
#fsave_vertices = [np.arange(10242), np.arange(10242)]
#morph_mat = compute_morph_matrix('9367', 'fsaverage', sample_vertices,
#                                 fsave_vertices, 20, subjects_dir)
#print morph_mat.shape
#print "Jane Here Here Here Here"                                  
#n_vertices_fsave = morph_mat.shape[0]
#
##    We have to change the shape for the dot() to work properly
#X = X.reshape(n_vertices_sample, n_times * n_subjects * 2)
#
#print np.shape(X)
#print('Morphing data.')
#X = morph_mat.dot(X)  # morph_mat is a sparse matrix
#X = X.reshape(n_vertices_fsave, n_times, n_subjects, 2)
#print np.shape(X)
#
##    Finally, we want to compare the overall activity levels in each condition,
##    the diff is taken along the last axis (condition). The negative sign makes
##    it so condition1 > condition2 shows up as "red blobs" (instead of blue).
#X = np.abs(X)  # only magnitude
#X = X[:, :, :, 0] - X[:, :, :, 1]  # make paired contrast
#print "Overall activity - difference in activity across conditions.."
#print np.shape(X)
#
################################################################################
## Compute statistic
#
##    To use an algorithm optimized for spatio-temporal clustering, we
##    just pass the spatial connectivity matrix (instead of spatio-temporal)
#print('Computing connectivity.')
#connectivity = spatial_tris_connectivity(grade_to_tris(5))
#
##    Note that X needs to be a multi-dimensional array of shape
##    samples (subjects) x time x space, so we permute dimensions
#X = np.transpose(X, [2, 1, 0])
#print np.shape(X)

################################################################################3
###################################################################################3333333
########################################################################################
## Transform to common cortical space
#
##    Normally you would read in estimates across several subjects and morph
##    them to the same cortical space (e.g. fsaverage). For example purposes,
##    we will simulate this by just having each "subject" have the same
##    response (just noisy in source space) here. Note that for 7 subjects
##    with a two-sided statistical test, the minimum significance under a
##    permutation test is only p = 1/(2 ** 6) = 0.015, which is large.
#n_vertices_sample, n_times = condition1.data.shape
#n_subjects = 7
#print('Simulating data for %d subjects.' % n_subjects)
#
##    Let's make sure our results replicate, so set the seed.
#np.random.seed(0)
#X = randn(n_vertices_sample, n_times, 2) * 10
#print X.shape 
#print np.newaxis
#X[:, :, 0] += condition1.data#[:, np.newaxis]
#X[:, :, 1] += condition2.data#[:, np.newaxis]
#
##    It's a good idea to spatially smooth the data, and for visualization
##    purposes, let's morph these to fsaverage, which is a grade 5 source space
##    with vertices 0:10242 for each hemisphere. Usually you'd have to morph
##    each subject's data separately (and you might want to use morph_data
##    instead), but here since all estimates are on 'sample' we can use one
##    morph matrix for all the heavy lifting.
#fsave_vertices = [np.arange(10242), np.arange(10242)]
#morph_mat = compute_morph_matrix('9367', 'fsaverage', sample_vertices,
#                                 fsave_vertices, 20, subjects_dir)
#print morph_mat.shape
#print "Jane Here Here Here Here" 
#n_vertices_fsave = morph_mat.shape[0]
#
##    We have to change the shape for the dot() to work properly
#X = X.reshape(n_vertices_sample, n_times * 2)
#
#print np.shape(X)
#print('Morphing data.')
#X = morph_mat.dot(X)  # morph_mat is a sparse matrix
#X = X.reshape(n_vertices_fsave, n_times, 2)
#print np.shape(X)
#
##    Finally, we want to compare the overall activity levels in each condition,
##    the diff is taken along the last axis (condition). The negative sign makes
##    it so condition1 > condition2 shows up as "red blobs" (instead of blue).
#X = np.abs(X)  # only magnitude
#X = X[:, :, 0] - X[:, :, 1]  # make paired contrast RED - CONDITION 1, BLUE - CONDITION 2
#print "Overall activity - difference in activity across conditions.."
#print np.shape(X)
##
#################################################################################
## Compute statistic
#
##    To use an algorithm optimized for spatio-temporal clustering, we
##    just pass the spatial connectivity matrix (instead of spatio-temporal)
#print('Computing connectivity.')
#connectivity = spatial_tris_connectivity(grade_to_tris(5))
#print np.shape(connectivity)
##
##    Note that X needs to be a multi-dimensional array of shape
##    samples (subjects) x time x space, so we permute dimensions
#print np.shape(X)
#X = np.transpose(X, [1, 0])
#print "after transposing........"
#print np.shape(X)