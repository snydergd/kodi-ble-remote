# Title
Kodi BLE control

# Status
This is a work in progress.  I recommend looking at `main.py` and adapting to your needs.

# Summary
I have a HiLetgo ESP32 dev board with oled display - model wtit-wb32 v2.  Here is a link to [the v3 version on Amazon](https://www.amazon.com/HiLetgo-Display-Bluetooth-Internet-Development/dp/B07DKD79Y9)

I want to use it as a control for Kodi through Bluetooth Low Energy (BLE).

Why?  Because I hooked up Kodi as my car's rear entertainment system, and I want to be able to pause the movie, see what's playing, or play some music, from the front of the car.

- Instantaneous press = go down one.
- Not-instantaneous press = select
- Long press = up
- Really long (1 second) press = previous menu

# How it works
Quick primer on BLE (from what I've gathered): The top level concept in BLE is a "Service", and BLE devices can have multiple.  A teapot might have a teapot service and a battery service.  Each service has a uuid identifying it, so that your teapot app on your phone can find the teapot.  Each service has "Characteristics" that you can interact with.  Your teapot service might have "temperature" and "setpoint" characteristics.  These too have uuids that an app could look for.  They also have "properties" -- essentially tags indicating how you can interact with the service (there's a finite set, including "read", "write", "notify").  Finally, there are "descriptors", which hold metadata about your characteristics.  So when you check the temperature of your teapot on your phone, you are simply reading the temperature characteristic of your teapot's BLE teapot service.

Here, my ESP32 exposes a serial connection through two characteristics (one for read, and another for write).

Through this wire, I send display update commands (in a format similar to G-code), and receive button push events.

Essentially the ESP32 is a dummy terminal with a single button.

The python script renders menus (and also supports rendering fancier visuals using pygame, but there's a big lag here I haven't figured out yet), interprets user input events, and communicates with Kodi.

# Setup
## Kodi side of things
Folder: `controlpy`

Install `pipenv` and then `pipenv run python main.py`.  Ideally set up a systemd unit or your preferred alternate to do this, for launching at startup, logging, etc.  Right now it is made to run on the same machine where Kodi is running.  In Kodi, make sure you have gone to `Settings -> Services` and enabled remote control (with username/pass of "kodi" - or else update the script with better values - in my disconnected car case, it doesn't matter).

This has only been tested on Linux/Bluez, but in theory it can probably also support other operating systems, since it uses the `ble-serial` library which attempts to support these different platforms, as well as `pykodi`, which is just network and shouldn't depend on these.

## ESP32 side of things
Folder: `Kodi-Buttons`

In my case I hooked up a 3000mAh battery to it, which is kind of neat for being able to tote it around while you work on it, but that doesn't matter.  You could just have it plugged in in your car the whole time, too.  I am just using the on-board pgm button (pin 0 on my board).

Tweak the `platformio.ini` file with your exact board (in my case, I'm using the v2 version), and possibly your serial/comm port.

Use your choice of platformio tooling.  In my case I use vscode and use the "Upload and Monitor" option to build and upload the code and view the output while working on it.

# TODO

- Better service UUIDs
- Alphabetical selector (letter ranges (a-f, g-l, ...), letters (g, h, i, ...), then individual titles)
- Other media - (TV Shows, Music, etc.)
- Favorites
- Package as zipapp
