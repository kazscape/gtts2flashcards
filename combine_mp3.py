import os
import shutil
import glob
import sox

os.mkdir('making_temp')

tfm = sox.Transformer()
tfm.pad(0.0,3.0)

files = glob.glob('./jllepd/b*.mp3')

for file in files:
    tfm.build(file,'./making_temp/' + os.path.basename(file))

files = sorted(glob.glob('./making_temp/*.*'))
cbn = sox.Combiner()
cbn.convert(samplerate=44100, n_channels=2)
cbn.build(files, './Bb.mp3', 'concatenate')

shutil.rmtree('making_temp')