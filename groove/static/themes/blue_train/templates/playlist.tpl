<!doctype html>
<html lang="en">
<head>
  <title>{{playlist['name']}} - Groove On Demand</title>

  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{{playlist['name']}}: {{playlist['description']}}">

  <meta name="og:title" content="{{playlist['name']}}">
  <meta name="og:description" content="{{playlist['description']}}">
  <meta name="og:url" content="{{playlist['url']}}">
  <meta name="og:type" content="audio">
  <meta name="og:provider_name" content="Groove on Demand">
  <meta name="og:image" content="/static/45.svg">

  <link rel='stylesheet' href='/static/styles.css' />
  <link rel='stylesheet' href="https://fonts.cdnfonts.com/css/clarendon-mt-std" />

  <link rel="apple-touch-icon" sizes="180x180" href="/static/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">

  <script defer crossorigin src='https://cdnjs.cloudflare.com/ajax/libs/howler/2.2.3/howler.core.min.js'></script>
  <script defer src='/static/player.js'></script>
  <script>
      var playlist_tracks = [
        % for entry in playlist['entries']:
        {
            title: "{{entry['artist']}} - {{entry['title']}}",
            url: "{{entry['url']}}",
        },
        % end
      ];
  </script>
</head>
<body>
<div id='container'>

    <div id='details'>
        <div id='poster'>
            <img src=''></img>
        </div>
        <div>
            <h1 id='playlist_title'>{{playlist['name']}}</h1>
            <span id='playlist_desc'>{{playlist['description']}}</span>
        </div>
    </div>

    <table id='player'>
    <tr>
        <td id='controls'>
            <div id='big_button' class='btn'>
                <div id="loading"></div>
                <div id="playBtn"></div>
                <div id="pauseBtn"></div>
            </div>
        </td>
        <td>
            <div id="track"></div>
            <div id='track_controls'>
                <div class='widget' id="timer">0:00</div>
                <div class='widget' id="bar">
                    <hr>
                    <div id="progress"></div>
                </div>
                <div class='widget' id="duration">0:00</div>
                <div class="widget btn" id="prevBtn">⏮</div>
                <div class="widget btn" id="nextBtn">⏭</div>
            </div>
        </td>
    </tr>
    </table>
    <div id="playlist">
        <div id="list"></div>
    </div>
    <div id='footer'>groove on demand : an <a alt="evilchili at liner notes dot club" href="https://linernotes.club/@evilchili">@evilchili</a> jam</div>
  </div>
</div>
</body>
</html>
