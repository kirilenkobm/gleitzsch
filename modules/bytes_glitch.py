"""Pre-process the image as a bytes string."""


def jpeg_header(bytez):
    """Get a terminal byte of jpeg header."""
    result = 0
    for i in range(len(bytez)):
        if bytez[i] == 255 and bytez[i + 1] == 218:
            result = i + 2
            break
    return result


def _glitch_bytes(image_file, output_file, amount_percent=0.3, seed_percent=0.5, iteration_count=9):
    """Glitch an image at the level of the file structure."""
    with open(image_file, "rb") as f:
        content = bytearray(f.read())

    header_length = jpeg_header(content)
    max_ind = len(content) - header_length - 4

    for i in range(iteration_count):
        min_pixel_index = int((max_ind / iteration_count * i)) | 0
        max_pixel_index = int((max_ind / iteration_count * (i + 1))) | 0

        delta = max_pixel_index - min_pixel_index
        pixel_index = int((min_pixel_index + delta * seed_percent)) | 0
        pixel_index = max_ind if pixel_index > max_ind else pixel_index

        indexInByteArray = ~~(header_length + pixel_index)
        print(content[indexInByteArray])
        content[indexInByteArray] = ~~int((amount_percent * 255))
        print(content[indexInByteArray])

    bytez_str = bytes(content)
    with open(output_file, "wb") as f:
        f.write(bytez_str)


def glitch_bytes(input_file, output_file, amountPercent=0.3, seedPercent=0.5, iterationCount=9):
    with open(input_file, 'rb') as f:
        bytez = bytearray(f.read())

    headerLength = jpeg_header(bytez)
    maxInd = len(bytez) - headerLength - 4

    for i in range(iterationCount):

        minPixelIndex = int((maxInd / iterationCount * i)) | 0
        maxPixelIndex = int((maxInd / iterationCount * (i + 1))) | 0
        delta = maxPixelIndex - minPixelIndex
        pixelIndex = int((minPixelIndex + delta * seedPercent)) | 0

        if pixelIndex > maxInd:
            pixelIndex = maxInd

        indexInByteArray = ~~(headerLength + pixelIndex)
        bytez[indexInByteArray] = ~~int((amountPercent * 255))

    bytez_str = bytes(bytez)

    with open(output_file, "wb") as f:
        f.write(bytez_str)
