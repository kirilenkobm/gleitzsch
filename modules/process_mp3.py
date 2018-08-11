"""Mp3 file processing module."""
from pydub import AudioSegment
import random


def parts(lst, n=25):
    """Split a list into a list of lists of len n."""
    return [lst[i:i + n] for i in iter(range(0, len(lst), n))]


def process_mp3(mp3_file, dimensions, chan_num=0):
    """Add glitches to a mp3 file itself."""
    # get size of image
    x, y = int(dimensions.split()[0]), int(dimensions.split()[1])
    # read the mp3
    sound = AudioSegment.from_mp3(mp3_file)
    sound_array = sound.get_array_of_samples()[:x * y]
    # go row by row
    # TODO optimize, customize
    for num, inds in enumerate(parts(list(range(len(sound_array))), n=x)):
        if num % 2 != 0:
            continue
        for inum, ind in enumerate(inds):
            if chan_num == 0:
                sound_array[ind] = sound_array[ind - x * num % 10]
            elif chan_num == 1:
                sound_array[ind] = sound_array[ind - x * num % 11]
            elif chan_num == 2:
                sound_array[ind] = sound_array[ind - x * num % 12]

    # save sound back
    new_sound = sound._spawn(sound_array)
    new_sound.export(mp3_file, format='mp3')

