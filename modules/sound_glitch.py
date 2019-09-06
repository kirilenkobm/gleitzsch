"""Modify intermediate MP3 file."""
import random
from array import array
import numpy as np
from pydub import AudioSegment


def parts(lst, n=25):
    """Split an iterable into list of iterables of size n."""
    return [lst[i:i + n] for i in iter(range(0, len(lst), n))]


def _process_layer(layer, shape, layer_num, mode="standart"):
    """Modify pseudo-color layer."""
    x, y = shape[0], shape[1]
    # if layer_num != 0:
    #     return np.reshape(layer, (x, y, 1))
    rows = [np.reshape(layer[:, i], (x, 1)) for i in range(y)]
    for num, row in enumerate(rows):
        # if num % 10 == 0:
        #     continue
        # rows[num] += rows[num - 1] // 20
        # rows[num] = rows[num - 1] if num % 2 == 0 else rows[num]
        if mode == "standart":
            rows[num] = np.roll(rows[num], num % 20, axis=0) if layer_num == 0 else rows[num]
            rows[num] = np.roll(rows[num], num % 30, axis=0) if layer_num == 1 else rows[num]
            rows[num] = np.roll(rows[num], num % 40, axis=0) if layer_num == 2 else rows[num]
    new_layer = np.reshape(np.concatenate(rows, axis=1), (x, y, 1))
    return new_layer


def process_layer(layer, layer_num, shape, mode="standart"):
    """Modify pseudo-color layer."""
    x, y = shape
    for num in range(len(layer)):
        layer[num] = num // 100 if layer_num == 1 else layer[num]
    # for num, inds in enumerate(parts(list(range(len(layer))), n=y)):
    #     if num % 2 != 0:
    #         continue
    #
    #     for inum, ind in enumerate(inds):
    #         if mode == "standart":
    #             if layer_num == 0:
    #                 layer[ind] = layer[ind - y * 1]
    #             elif layer_num == 1:
    #                 layer[ind] = layer[ind - y * 2]
    #             else:
    #                 layer[ind] = layer[ind - y * 3]
    #         elif mode == "second":
    #             ct = random.choice(range(10, 40))
    #             if layer_num == 0:
    #                 layer[ind] = layer[ind - x * num % ct]
    #             elif layer_num == 1:
    #                 layer[ind] = layer[ind - x * num % ct]
    #             else:
    #                 layer[ind] = layer[ind - x * num % ct]
    #         elif mode == "third":
    #             if layer_num == 0:
    #                 layer[ind] = layer[ind - x * num % 11]
    #             elif layer_num == 1:
    #                 layer[ind] = layer[ind - x * num % 12]
    #             else:
    #                 layer[ind] = layer[ind - x * num % 10]
    #         else:
    #             pass
    return layer


def process_mp3(sound_file, im_shape, output=None):
    """Glitch mp3."""
    output = output if output else sound_file
    x, y = im_shape
    chan_size = x * y
    last_ind = x * y * 3

    sound = AudioSegment.from_mp3(sound_file)
    sound_array = np.array(sound.get_array_of_samples()[:last_ind])
    # layers = [sound_array[i: i + (x * y)] for i in range(0, (x * y * 3), (x * y))]
    # layers = [array("h", np.reshape(sound_array, (x, y, 3))[:, :, i]) for i in range(3)]
    layers = []

    # print(sound_array.typecode)  # signed short 32768
    # layers_all = np.reshape(sound_array, (x, y, 3))
    # layers = [layers_all[:, :, i] for i in range(3)]
    processed_layers = []
    for num, layer in enumerate(layers):
        processed_layer = process_layer(layer, num, im_shape)
        processed_layers.extend(processed_layer)
    # concat = np.reshape(np.concatenate(processed_layers, axis=2), x * y * 3)
    new_array = array("h", processed_layers)
    new_sound = sound._spawn(new_array)
    new_sound.export(output, format='mp3')
    # return nothing


def _process_mp3(sound_file, shape, chnum=0, gmode=2):
    """Copy-pasted from the previous version.

    Actually pretty bad.
    """
    x, y = shape
    sound = AudioSegment.from_mp3(sound_file)
    sound_array = sound.get_array_of_samples()

    rshift = [1, 2, 3]
    random.shuffle(rshift)
    for num, inds in enumerate(parts(list(range(len(sound_array))), n=y)):
        if num % 2 == 0:
            if gmode == 0:
                pass

            elif gmode == 1:
                for inum, ind in enumerate(inds):
                    ct = random.choice(range(10, 40))
                    if chnum == 0:
                        sound_array[ind] = sound_array[ind - y * num % ct]
                    elif chnum == 1:
                        sound_array[ind] = sound_array[ind - y * num % ct]
                    else:
                        sound_array[ind] = sound_array[ind - y * num % ct]

            elif gmode == 2:

                for inum, ind in enumerate(inds):
                    if chnum == 0:
                        sound_array[ind] = sound_array[ind - y * rshift[0]]
                    elif chnum == 1:
                        sound_array[ind] = sound_array[ind - y * rshift[1]]
                    else:
                        sound_array[ind] = sound_array[ind - y * rshift[2]]

            else:
                for inum, ind in enumerate(inds):
                    if chnum == 0:
                        sound_array[ind] = sound_array[ind - y * num % 11]
                    elif chnum == 1:
                        sound_array[ind] = sound_array[ind - y * num % 12]
                    else:
                        sound_array[ind] = sound_array[ind - y * num % 10]

    new_sound = sound._spawn(sound_array)
    new_sound.export(sound_file, format='mp3')
