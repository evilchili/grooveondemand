<audio id="audio" preload="none" tabindex="0">
% for sig, track_id in args:
    <source src="/track/{{sig}}/{{track_id}}">
% end
    Your browser does not support HTML5 audio.
</audio>
