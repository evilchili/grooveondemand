# Groove On Demand

Groove on Demand is a self-hosted application for creating and sharing music playlists. It streams music directly from your local media library using HTML5 audio and a Javascript player built on [Howler.js](https://github.com/goldfire/howler.js) and features a robust interactive command-line tool for managing the playlist database.

`[ insert session capture here ]`

## Installation

### Prerequisites and Disclaimers

Groove on Demand was developed against python 3.10 and should work on anything 3.7 or above. Minimal testing was done on this front.

I have no idea if it will function on platforms besides Linux. Code was written to be portable but not tested to be portable. I also don't know if the dependencies support diverse platforms or not. `¯\_(ツ)_/¯`

### 1. Download and install the latest release

[ check the releases tab ]

```
pip3 install https://github.com/evilchili/grooveondemand/releases/download/beta/grooveondemand-0.9.tar.gz
```

### 2. Generate the default configuration

```
~/.local/bin/groove setup > ~/.groove
```

### 3. Set the Media Root

Edit `~/.groove` and define `MEDIA_ROOT` to point to the directory containing your local audio files. For example:

```
MEDIA_ROOT=/media/audio/lossless
```

## Setting up the Databse

Before creating playlists, you must scan your media and build a database of tracks. Do this by running:

```
groove scan
```

This may take a long time depending on the size of your library and the capabilities of your system. Progress will be displayed as the scan progresses:

<pre>
groove&gt; scan
1:27:34 <font color="#70BC45">━━━━━━━━━━━━━━━</font> <font color="#70BC45">100%</font> <font color="#555555">|</font> <font color="#70BC45"> 29946</font> <font color="#F1F2F6"><b>total</b></font> <font color="#555555">|</font> <font color="#70BC45"> 29946</font> <font color="#F1F2F6"><b>new</b></font> <font color="#555555">|</font>   <font color="#F1F2F6">Scan of </font><font color="#9999FF">/mnt/grunt/music/FLAC</font><font color="#F1F2F6"> complete!</font>
</pre>

## Start the Interactive Shell

Groove On Demand's interactive shell is optimized for quickly creating new playlists with as few keystrokes as possible. Start it by running:

```
groove shell
```

Use the `help` command to explore. 

## Serving Playlists

Start the web server application by running:

```
groove server
```

It is strongly recommended you place the app behind a web proxy.

## Okay, But Why?

Because I wanted Mixtapes-as-a-Service but without the hassle of dealing with a third party, user authentication, and related shenanigans. Also I hadn't written code in a few years and was worried I was forgetting how to do it. I am not entirely reassured on that point.
