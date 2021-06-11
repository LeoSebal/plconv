#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TODO
- dynamic export file name feature: config['output_file']
- parallelism
"""

import os
import argparse
import shutil
from pathlib import Path
import re
import yaml
import mutagen



def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("playlists", type=str, nargs="+",
                            help="Paths to playlists to convert")
    parser.add_argument("-o", "--out_dir",
                            help="Output directory")
    parser.add_argument("--preset",
                        help="Specify the preset.")
    parser.add_argument("--encoder",
                        help="Specify the encoder. /!\\ The preset must match the encoder!")
    parser.add_argument("-v", "--verbose", action="store_true",
                            help="Verbosity")
    parser.add_argument("-v2", "--extra_verbose", action="store_true",
                            help="Extra verbosity")
    parser.add_argument("--no_playlists", action="store_true",
                            help="Skip the playlist export")
    parser.add_argument("--export_playlists", action="store_true",
                            help="Export the conversion playlist")
    args = parser.parse_args()

    # Quick check
    if not (not args.no_playlists) ^ args.export_playlists:
        raise ValueError("Incompatible arguments: --no_playlists --export_playlists")
    return args



def load_config(config_path:Path=Path("config.yaml")):
    """
    Load configuration file from path, or fallback to default parameters

    Parameter
    ---------
    config_path: Path
        Path to a configuration file. Default: "config.yaml"
    
    Returns
    -------
    config: dict
        The dictionary
    """
    with open("config_default.yaml") as fid:
        config = yaml.safe_load(fid)
    if config_path.exists:
        with open(config_path) as fid:
            imported_config = yaml.safe_load(fid)
    for field in imported_config:
        config[field] = imported_config[field]
    # Convert paths to Path format
    config['out_dir'] = Path(config['out_dir'])
    return config



def set_args(args:argparse.ArgumentParser, config):
    """
    Overrule current configuration with input args

    args: argparse.ArgumentParser
        The input arguments
    config: dict
        The config
    """
    if args.out_dir:
        config["out_dir"] = args.out_dir
    if args.encoder:
        config["encoder"] = args.encoder
    if args.preset:
        config["preset"] = args.preset
    if args.verbose:
        config["verbose"] = 1
    if args.extra_verbose:
        config["verbose"] = 2
    if not args.no_playlists or args.export_playlists:
        config["export_playlist"] = True
    # Check playlist existence
    playlists = args.playlists
    for playlist in playlists:
        if not Path(playlist).exists():
            playlists.pop(playlist)
            print(f"{playlist} not found")
    return playlists



def import_playlist(playlist:list, config):
    """
    Imports a playlist as a list of mutagen.File files

    Parameter
    ---------
    playlist: list
        List of paths to audio files

    Returns
    -------
    audiofiles: list
        List of audio files
    """
    audiofiles = []
    with open(playlist, "r", encoding="utf-8") as fid:
        line = fid.readline()
        while line:
            if Path(line.replace("\n","")).exists():
                audiofile = mutagen.File(line.replace("\n", ""))
                if type(audiofile.tags) is mutagen.id3.ID3:
                    audiofile = mutagen.easyid3.EasyID3(line.replace("\n", ""))
                audiofiles.append(audiofile)
            elif config["verbose"]:
                print(f"File not found: {line}")
            line = fid.readline()
    return audiofiles



def set_output_name(audiofile, config=None):
    """
    Sets the output file name. Currently, only $artist - $title is supported
    TODO: complete for dynamic export title

    Parameters
    ----------
    audiofile: mutagen.File
        File from which extract the metadata
    config: dict
        Current configuration

    Returns
    -------
    filename: str
        Output filename, without the extension (default: $artist - $title)
    """
    artist = (audiofile['artist'] if 'artist' in audiofile else ["Unknown Artist"])
    title = (audiofile['title'] if 'title' in audiofile else ["Untitled"])
    filename = "{} - {}".format(*artist, *title)
    # Replace forbidden path characters
    filename = re.sub("[<>/\\|?\*]", "_", filename)
    filename = filename.replace(":", "-")
    filename = filename.replace("\"", "'")
    return filename



def convert(audiofile, config, preset, overwrite:bool=False):
    """
    Converts audiofile to the chosen `preset` format
    TODO implement `overwrite` option

    Returns
    -------
    path_out: str
        Path to the newly created file
    """
    filename_out = set_output_name(audiofile, config)
    path_out = config['out_dir'] / filename_out
    encoder_args = config['presets'][preset].replace("$input", Path(audiofile.filename).as_posix()).replace("$output", path_out.as_posix())
    ext = re.findall("\\$output(\\.[a-zA-Z0-9]*)", config["presets"][preset])[0]  # extension from preset
    opts = {'ffmpeg': ("-n", "-loglevel 0")}  # supplementary encoder options

    # Skip conversion if source is mp3 or source and target are the same
    if Path(audiofile.filename).suffix in (".mp3", ext):
        shutil.copy2(audiofile.filename, config['out_dir'] / (filename_out + ext))
        if config['verbose']:
            print(f"\t{filename_out + ext} copied")

    elif overwrite:
        raise NotImplementedError

    else:
        if not path_out.with_suffix(ext).exists():
            command = config['encoder'] + " " + encoder_args
            if config['encoder'] in opts:
                command = " ".join([command, *opts[config['encoder']]])
            ret = os.system(command)
            if config['verbose'] & ret!=0:
                print(f"\tFailed to convert {audiofile.filename} to {preset}")
            if config['verbose']:
                print(f"\t{filename_out + ext} converted")
        elif config['verbose']:
            print(f"\t{filename_out + ext} already exists, skipping conversion")

    return filename_out + ext



if __name__ == '__main__':

    args = argparser()
    config = load_config()
    playlists = set_args(args, config)

    if not config['out_dir'].exists():
        config['out_dir'].mkdir()

    for playlist in playlists:

        audiofiles = import_playlist(playlist, config)

        playlist_out = Path(Path(playlist).stem + ".m3u8")
        if config["verbose"]:
            print(f"Treating: {Path(playlist).stem}")
        if config["export_playlists"] and (config['out_dir'] / playlist_out).exists():
            with open(config['out_dir'] / playlist_out, "w", encoding="utf-8") as fid:
                print("", end="", file=fid)
            if config['verbose']:
                print(f"Deleting former playlist file: {playlist_out.parts[-1]}")

        for audiofile in audiofiles:
            out_pl = Path(playlist).stem + '.m3u8'
            path_out = convert(audiofile, config, config["preset"])
            if config["export_playlists"]:
                with open(config["out_dir"] / playlist_out, "a", encoding="utf-8") as fid:
                    print(path_out, file=fid)

        if config['verbose']:
            print(f"Written: {config['out_dir'] / playlist_out}")

    if config['verbose']:
        print("Done")
