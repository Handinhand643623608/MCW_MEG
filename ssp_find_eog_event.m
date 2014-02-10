function ssp_find_eog_event(subjID, exprum)

%input file
%in_fif_File = infif;
%EOG Event file
%[~, name, ~] = fileparts(infif);
% [name1, remain]= strtok(name, '_');
% [name2, ~]=strtok(remain, '_');
% eog_eventFileName = [inpath, name1,'_', name2, '_eog-eve.fif'];


inpath = '/home/custine/MEG/data/msabri/';

in_fif_File = [inpath subjID '/' subjID '_' exprum,'_raw.fif'];
%in_fif_File = [inpath '/data/' subjID '/' subjID '_ATLLoc_raw.fif'];
eog_eventFileName = [inpath subjID '/ssp/' subjID '_' exprum,'_eog-eve.fif'];

%reading eog channels from data files
[fiffsetup] = fiff_setup_read_raw(in_fif_File);
channelNames = fiffsetup.info.ch_names;
ch_EOG = strmatch('EOG',channelNames);
sampRate = fiffsetup.info.sfreq;
start_samp = fiffsetup.first_samp;
end_samp = fiffsetup.last_samp;
[eog] = fiff_read_raw_segment(fiffsetup, start_samp ,end_samp, ch_EOG(1));

% Detecting Blinks
filteog = eegfilt(eog, sampRate,0,10);
EOG_type = 202;
firstSamp = fiffsetup.first_samp;
temp = filteog-mean(filteog);
 
eog_std_dev_value=1; %Change according to the subject(Default 1) (Higher number- detect only distict narrow peaks) 

if sum(temp>(mean(temp)+1*std(temp))) > sum(temp<(mean(temp)+1*std(temp)))
    
    eog_events = peakfinder((filteog),eog_std_dev_value*std(filteog),-1);

else
    eog_events = peakfinder((filteog),eog_std_dev_value*std(filteog),1);

end


writeEventFile(eog_eventFileName, firstSamp, eog_events, EOG_type);

end
