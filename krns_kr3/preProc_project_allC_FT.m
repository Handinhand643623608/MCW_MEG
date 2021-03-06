function preProc_project_allC_FT(subjID, sessID, run)

%Wrapper Script to run the ICA analysis on the Neuromag Raw.fif input file.
%Computes the first 20 ICA componenets of the specified input and plots the
%components as a time series. After running this script, check the
%Component topoplot figue and identify the artifacts you would like to
%reject. See the fieldtrip website for information on how to identify your
%artifacts. 

%Author: Candida Jane Maria Ustine, custine@mcw.edu
%Modified for krns_kr3 study on 07/29/2014 
%Usage: preProc_project_allC_FT('9444', 's1', 'run1')

%% Initialise Fieldtrip Defaults 
ft_defaults

%% Initialise Subject Specific Defaults  
inpath = ['/home/custine/MEG/data/krns_kr3/', subjID, '/', sessID, '/'];
fiff = strcat(inpath, subjID,'_',sessID, '_', run, '_raw.fif')
comp_file = strcat(inpath,'ssp/fieldtrip/', subjID,'_',sessID,'_', run,'_allC_comp.mat')

Fevents = ft_read_event(fiff);
[len, ~] = size(Fevents);
F = [];
endS = []

%% OPTION 1: Keep this (and comment out OPTION 2) IF you are proceeding with Averaging after ICA analysis. 
for i = 1:len
       F = [F, Fevents(i).sample];
end

% % %For the whole time window of the raw file (same as Option 2 below) 
% F = F'
% [len, ~] = size(F);
% begS = F(1,1)
% endS = F(len,1)
% samples = horzcat(begS, endS, 0)

%Short samples - all trials... 
F = F';
[len, ~] = size(F);
begS = F(:,1);
begS = begS(1:len-1);
for i = 1:size(begS)-1;
    endS(i) = (begS(i+1)); %%1118 samples
end
endS(i+1) = endS(i) +10000
offset = zeros(1,len-1);
size(endS)
size(begS)
samples = horzcat(begS, endS', offset')

% % %% OPTION 2: Keep this (and comment out OPTION 1) If you are writing the data structure after ICA analysis back to a fiff file
% % for i = 1:len
% %        F = [F, Fevents(i).sample];
% % end
% % F = F';
% % [len, ~] = size(F);
% % begSt = F(1) 
% % endSt = F(len)
% % offsett = 0
% % samples = horzcat(begSt, endSt, offsett)% % the original data can now be reconstructed, excluding those components
% load(comp_file)
% cfg = [];
% cfg.component = [8 10];
% data_clean = ft_rejectcomponent(cfg, comp, data); %using the non sampled data :) (use the sampled data when you want to write back to a fif) 
% save(comp_file, 'data_clean', 'comp', 'data', 'cfg')


%% Define Trials 
dat = ft_read_data(fiff);
hdr = ft_read_header(fiff);
cfg = []
cfg.trl = samples
% cfg.trialdef.prestim = -0.1
% cfg.trialdef.poststim = 3
% cfg.trialdef.eventvalue = 1 % Standard trigger value
cfg.headerfile = fiff
cfg.inputfile = fiff
cfg.trl.dataset = fiff
cfg.dataset = fiff
cfg = ft_definetrial(cfg)
cfg.trl = samples

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% % % Reject Artifacts
% % cfg = ft_rejectartifact(cfg)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ICA To Remove ECG Artifacts
cfg.trialdef.eventtype = 'all'

%remove all jump and muscle artifacts before running your ICA
cfg = ft_artifact_jump(cfg)
[meg] = ft_channelselection('all', hdr.label) %% NOTE: MUST BE ALL CHANNELS FOR THE FT_PREPROCESSING STEP AND THEN WHEN YOU ARE DOING THE ICA YOU CAN JUST COMPUTE ON THE MAGNETOMETERS OR ALL MEG CHANNELS… :) IMPORTANT!!! 
%cfg.channel = {'all', '-refchan'};
cfg.channel = meg
cfg.layout    = 'neuromag306mag.lay'
cfg.trl = samples


% You can now preprocess the data:
data = ft_preprocessing(cfg)

% %Reject Visual Trials and see the epoched response: (Optional) 
% data_clean   = ft_rejectvisual(cfg, data);

% % %you should downsample your data before continuing, otherwise ICA decomposition will take too long
% data_orig = data
% cfg = []
% cfg.resamplefs = 300
% cfg.detrend = 'no'
% data = ft_resampledata(cfg, data)

%% Set the ICA method 
cfg            = []; % the original data can now be reconstructed, excluding those components
cfg.method = 'fastica';
%cfg.channel = {'all', '-refchan'};
[meg] = ft_channelselection('MEG', hdr.label)
%[meg] = ft_channelselection('MEGGRAD', hdr.label)
cfg.channel = [meg]
%cfg.runica.pca = 101 % number of magnetometers -1
comp = ft_componentanalysis(cfg, data);

%% Plot the ICA Components 
%Look at the topography of the components. http://fieldtrip.fcdonders.nl/template/layout

cfg = [];
cfg.component = [1:20];       % specify the component(s) that should be plotted
cfg.layout    = 'neuromag306mag.lay'; % specify the layout file that should be used for plotting: mag/planar/all
cfg.comment   = 'no';
[cfg] = ft_topoplotIC(cfg, comp)

%Look at their time courses
cfg = []
cfg.channel = [1:20]
cfg.viewmode = 'component'
cfg.layout = 'neuromag306mag.lay'
ft_databrowser(cfg, comp)
 
save(comp_file, 'cfg', 'data', 'comp','comp_file')


% the original data can now be reconstructed, excluding those components
% load(comp_file)
cfg = [];
cfg.component = [8 13];
data_clean = ft_rejectcomponent(cfg, comp, data); %using the non sampled data :) (use the sampled data when you want to write back to a fif) 
save(comp_file, 'data_clean', 'comp', 'data', 'cfg')

end
