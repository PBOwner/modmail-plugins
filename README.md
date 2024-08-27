<h1 align="center"><img src="https://files.catbox.moe/92mfqx.png"></h1>
<div align="center">
 <a href="https://github.com/raidensakura"><img src="https://img.shields.io/badge/modmail--plugins-by%20Raiden-d11df9"></a>
 <a href="https://github.com/Cog-Creators/Red-DiscordBot"><img src="https://img.shields.io/badge/Modmail%20-V4-cyan.svg"></a>
 <a href="[https://github.com/raidensakura](https://github.com/python/black)"><img src="https://img.shields.io/badge/code%20style-black-1c1c1c.svg"></a>
 <a href="https://dsc.gg/transience/"><img src="https://discord.com/api/guilds/616969119685935162/widget.png"></a><br>
 <a href="https://ko-fi.com/P5P6D65UW"><img src="https://storage.ko-fi.com/cdn/brandasset/kofi_button_red.png" style="height: 25px;"></a>
</div>
<br>
<p align="center">A collection of <strike>badly written</strike> plugins for Python Discord Modmail bot.</p>

<h2 align="center">Installation</h2>

Make sure to set `REGISTRY_PLUGINS_ONLY` in your environment variables to `False` otherwise installation will fail.

```ini
[p]plugin install raidensakura/modmail-plugins/[plugin_name]@main
[p]plugin load raidensakura/modmail-plugins/[plugin_name]@main
```

<h2 align="center">List of Plugins</h2>

<table align="center">
 
 <thead>
  <tr>
   <td>Name</td>
   <td>Description</td>
  </tr>
 </thead>
 
 <tr>
  <td><a href="https://github.com/raidensakura/modmail-plugins/tree/main/logviewer">Logviewer</a></td>
  <td>A modification of <a href="https://github.com/Jerrie-Aries/modmail-plugins/tree/master/logviewer">Jerrie-Aries' logviewer plugin</a> with OAuth support and a log list page.<br><br>To enable OAuth, make sure these variables exist in your environment:
  <ul>
  <li><code>OAUTH2_CLIENT_ID</code> - The ID of your bot</li>
  <li><code>OAUTH2_CLIENT_SECRET</code> - Get this from the general information section of your bot app in the Discord dev portal</li>
  <li><code>OAUTH2_REDIRECT_URI</code> - This will be equal to the URL of your log viewer app + <code>/callback</code> e.g. <code>https://logwebsite.com/callback</code>. You will need to add this same URL as a redirect URL in the OAuth2 section in the Discord dev portal.<br></li>
  </ul>Lastly, add users or roles to whitelist to access the logs with <code>[p]oauth whitelist @user/role</code>
  </td>
 </tr>

 <tr>
  <td><a href="https://github.com/raidensakura/modmail-plugins/tree/main/say">Say</a></td>
  <td>A port of <a href="https://github.com/laggron42/Laggrons-Dumb-Cogs/tree/v3/say">El Laggron's say cog</a> for Red Discord bot with some incompatible features removed.</td>
 </tr>

 <tr>
  <td><a href="https://github.com/raidensakura/modmail-plugins/tree/main/video-preview">Video Preview</a></td>
  <td>Bounty plugin made for neya. It simply sends a link of a video attachment inside the thread channel so it can be played within the client.</td>
 </tr>
 
</table>

<h2 align="center">Dev Stuff</h2>

<h3 align="center">Formatting</h3>
<p align="center">Make sure poetry is installed (I recommend using pipx).</p>

```py
poetry install --no-root --only dev
pre-commit install
```

<h2 align="center">Credits</h2>

<p align="center">
 <ul>
  <li><a href="https://github.com/modmail-dev">modmail-dev</a> for Modmail bot and parts of the OAuth codes.</li>
  <li><a href="https://github.com/Jerrie-Aries">Jerrie-Aries</a> for the original logviewer plugin.</li>
 </ul>
</p>
