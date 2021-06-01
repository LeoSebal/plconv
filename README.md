# plconv - Playlist converter

This Python 3 script was made in order to export a list of .m3u or .m3u8 files, and convert its input to the chosen format. I wrote this script to be able to quickly export my DJ playlists to formats compatible with most hardware: this is why the default configuration only supports MP3 and AIFF conversion.

All converted files are renamed `<artist> - <title>.ext`. Duplicates will be skipped.

It has been tested on Windows.

## Installation

1. Install mutagen: `pip install mutagen`
2. Clone this repository

## Usage

```
playlistconvert playlist1.m3u [playlist2.m3u ...] [-o <output_directory>] [--preset <preset>] [--encoder] [-v] [-v2] [--no_playlists] [--export_playlists]
```

* `--preset <preset`: choose your preset (default: mp3-v0)
* `--encoder <encoder>`: choose your encoder from the `config.yaml` file (default: ffmpeg)
* `-v`, `-v2`: activate verbosity levels 1 or 2
* `--export_playlists`: make a copy of the input playlist with the files just created (default)
* `--no_playlists`: do not make a copy of the input playlist

## Configuration customization

To create your own configuration, create a file called `config.yaml`, and put any of the settings you can find in `config_default.yaml` to overwrite them.

Currently, you can change the default playlist directory, add your custom presets and encoders, and change the default preset.

## Known bugs

1. Audio files are recognized by their output names. Therefore, if several tracks from a same artist bear the same title, they will not be identified as different, and only the first one will be converted. This behaviour is intended to allow the co-existence of the same track in several playlists, and avoid converting it again every time.

## TODO

1. Add conversion multithreading
2. Add customizable file output formats
3. Allow for different tracks with the same artist/title to be recognized uniquely