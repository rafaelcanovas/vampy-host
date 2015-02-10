'''A high-level interface to the vampyhost extension module, for quickly and easily running Vamp audio analysis plugins on audio files and buffers.'''

import vampyhost
import frames
import load

def process_with_initialised_plugin(ff, sample_rate, step_size, plugin, outputs):

    out_indices = dict([(id, plugin.get_output(id)["output_index"])
                        for id in outputs])
    plugin.reset()
    fi = 0

    for f in ff:
        timestamp = vampyhost.frame_to_realtime(fi, sample_rate)
        results = plugin.process_block(f, timestamp)
        # results is a dict mapping output number -> list of feature dicts
        for o in outputs:
            ix = out_indices[o]
            if ix in results:
                for r in results[ix]:
                    yield { o: r }
        fi = fi + step_size

    results = plugin.get_remaining_features()
    for o in outputs:
        ix = out_indices[o]
        if ix in results:
            for r in results[ix]:
                yield { o: r }


def process(data, sample_rate, key, output = "", parameters = {}):
    """Process audio data with a Vamp plugin, and make the results from a
    single plugin output available as a generator.

    The provided data should be a 1- or 2-dimensional list or NumPy
    array of floats. If it is 2-dimensional, the first dimension is
    taken to be the channel count.

    The returned results will be those calculated by the plugin with
    the given key and returned through its output with the given
    output identifier. If the requested output is the empty string,
    the first output provided by the plugin will be used.

    If the parameters dict is non-empty, the plugin will be configured
    by setting its parameters according to the (string) key and
    (float) value data found in the dict.

    This function acts as a generator, yielding a sequence of result
    features as it obtains them. Each feature is represented as a
    dictionary containing, optionally, timestamp and duration
    (RealTime objects), label (string), and a 1-dimensional array of
    float values.

    If you would prefer to obtain all features in a single output
    structure, consider using vamp.collect() instead.
    """

    plugin, step_size, block_size = load.load_and_configure(data, sample_rate, key, parameters)

    if output == "":
        output = plugin.get_output(0)["identifier"]

    ff = frames.frames_from_array(data, step_size, block_size)

    for r in process_with_initialised_plugin(ff, sample_rate, step_size, plugin, [output]):
        yield r[output]
    
    plugin.unload()


def process_frames(ff, sample_rate, step_size, key, output = "", parameters = {}):
    """Process audio data with a Vamp plugin, and make the results from a
    single plugin output available as a generator.

    The provided data should be an enumerable sequence of time-domain
    audio frames, of which each frame is 2-dimensional list or NumPy
    array of floats. The first dimension is taken to be the channel
    count, and the second dimension the frame or block size. The
    step_size argument gives the increment in audio samples from one
    frame to the next. Each frame must have the same size.

    The returned results will be those calculated by the plugin with
    the given key and returned through its output with the given
    output identifier. If the requested output is the empty string,
    the first output provided by the plugin will be used.

    If the parameters dict is non-empty, the plugin will be configured
    by setting its parameters according to the (string) key and
    (float) value data found in the dict.

    This function acts as a generator, yielding a sequence of result
    features as it obtains them. Each feature is represented as a
    dictionary containing, optionally, timestamp and duration
    (RealTime objects), label (string), and a 1-dimensional array of
    float values.

    If you would prefer to obtain all features in a single output
    structure, consider using vamp.collect() instead.
    """
    plugin = vampyhost.load_plugin(key, sample_rate,
                                   vampyhost.ADAPT_INPUT_DOMAIN +
                                   vampyhost.ADAPT_BUFFER_SIZE +
                                   vampyhost.ADAPT_CHANNEL_COUNT)

    fi = 0
    channels = 0
    block_size = 0

    if output == "":
        out_index = 0
    else:
        out_index = plugin.get_output(output)["output_index"]
    
    for f in ff:

        if fi == 0:
            channels = f.shape[0]
            block_size = f.shape[1]
            plugin.set_parameter_values(parameters)
            if not plugin.initialise(channels, step_size, block_size):
                raise "Failed to initialise plugin"

        timestamp = vampyhost.frame_to_realtime(fi, sample_rate)
        results = plugin.process_block(f, timestamp)
        # results is a dict mapping output number -> list of feature dicts
        if out_index in results:
            for r in results[out_index]:
                yield r

        fi = fi + step_size

    if fi > 0:
        results = plugin.get_remaining_features()
        if out_index in results:
            for r in results[out_index]:
                yield r
        
    plugin.unload()
    

def process_multiple_outputs(data, sample_rate, key, outputs, parameters = {}):
    """Process audio data with a Vamp plugin, and make the results from a
    set of plugin outputs available as a generator.

    The provided data should be a 1- or 2-dimensional list or NumPy
    array of floats. If it is 2-dimensional, the first dimension is
    taken to be the channel count.

    The returned results will be those calculated by the plugin with
    the given key and returned through its outputs whose identifiers
    are given in the outputs argument.

    If the parameters dict is non-empty, the plugin will be configured
    by setting its parameters according to the (string) key and
    (float) value data found in the dict.

    This function acts as a generator, yielding a sequence of result
    feature sets as it obtains them. Each feature set is a dictionary
    mapping from output identifier to a list of features, each
    represented as a dictionary containing, optionally, timestamp and
    duration (RealTime objects), label (string), and a 1-dimensional
    array of float values.
    """

    plugin, step_size, block_size = load.load_and_configure(data, sample_rate, key, parameters)

    ff = frames.frames_from_array(data, step_size, block_size)

    for r in process_with_initialised_plugin(ff, sample_rate, step_size, plugin, outputs):
        yield r

    plugin.unload()


def process_frames_multiple_outputs(ff, sample_rate, step_size, key, outputs, parameters = {}):
    """Process audio data with a Vamp plugin, and make the results from a
    set of plugin outputs available as a generator.

    The provided data should be an enumerable sequence of time-domain
    audio frames, of which each frame is 2-dimensional list or NumPy
    array of floats. The first dimension is taken to be the channel
    count, and the second dimension the frame or block size. The
    step_size argument gives the increment in audio samples from one
    frame to the next. Each frame must have the same size.

    The returned results will be those calculated by the plugin with
    the given key and returned through its outputs whose identifiers
    are given in the outputs argument.

    If the parameters dict is non-empty, the plugin will be configured
    by setting its parameters according to the (string) key and
    (float) value data found in the dict.

    This function acts as a generator, yielding a sequence of result
    feature sets as it obtains them. Each feature set is a dictionary
    mapping from output identifier to a list of features, each
    represented as a dictionary containing, optionally, timestamp and
    duration (RealTime objects), label (string), and a 1-dimensional
    array of float values.
    """
    plugin = vampyhost.load_plugin(key, sample_rate,
                                   vampyhost.ADAPT_INPUT_DOMAIN +
                                   vampyhost.ADAPT_BUFFER_SIZE +
                                   vampyhost.ADAPT_CHANNEL_COUNT)

    out_indices = dict([(id, plugin.get_output(id)["output_index"])
                        for id in outputs])
    
    fi = 0
    channels = 0
    block_size = 0

    for f in ff:

        if fi == 0:
            channels = f.shape[0]
            block_size = f.shape[1]
            plugin.set_parameter_values(parameters)
            if not plugin.initialise(channels, step_size, block_size):
                raise "Failed to initialise plugin"

        timestamp = vampyhost.frame_to_realtime(fi, sample_rate)
        results = plugin.process_block(f, timestamp)
        # results is a dict mapping output number -> list of feature dicts
        for o in outputs:
            ix = out_indices[o]
            if ix in results:
                for r in results[ix]:
                    yield { o: r }
        fi = fi + step_size

    if fi > 0:
        results = plugin.get_remaining_features()
        for o in outputs:
            ix = out_indices[o]
            if ix in results:
                for r in results[ix]:
                    yield { o: r }
        
    plugin.unload()


