## TL;DR Instructions

1. Take the diffuser and back case off the badge using the included allen wrench
2. Solder on the keyswitches
3. Solder on the battery holder.
4. Reasseble the diffuser + case
5. Flash the badge with the u2f firmware from github / link can be found on www.dczia.net

## Intro

Thanks for purchasing the 2026 DCZia “mk9” badge! This badge is a throwback to our earlier keygrid badge from 2018. The badge features 9 mechanical MX style key switches (Gateron Blues), an accelerometer for sensing movement and adjusting the light patterns, and the badge can function as a usb keyboard / macro pad. By default the badge will output the keystrokes 1-9 like a num pad, but you can modify the code or flash QMK to use a full programmable macropad if you want. The badge is powered by an RPI 2040 microcontroller, with a 16mb flash module for expansion. An accelerometer is included as well.

## Building

The badge is shipped with the frosted diffuser, and back case pre installed. You will need to remove these pieces to safely solder on the keyswitches. Use the included allan key to disassemble the case.

[]()

Now you can install one keyswitch, and solder it onto the board. Please go slow, and try to line up the switch carefully. Sometimes some tape can be useful to keep the switch in place. Solder on all 9 key switches.

Next solder on the battery pack. The red wire will go to the “+” pad on the back of the pcb, and the black wire to the “-” pad. The badge can be fully powered over USB C if you do not wish to attach the battery pack.

After the battery pack is installed, reassemble the case, and gently screw it back together. 

Next, using the round double sticky tape, apply it to the battery pack, and then stick it to the frosted diffuser. Press gently on the battery pack for about 15 seconds to make sure you have good adhesion.

Finally install the batteries. Goto www.dczia.net, and click on the badge to be taken to the Github page for this project. Download the release which will have the source code, and a u2f file. Plug the badge into your computer and hold down the “Boot” button on the badge while plugging it in. You will need a pen or toothpick to press in the switch while plugging in the USB C cable. This will place the badge into bootloader mode. A usb drive should appear on your machine if you are using something common (Win / Mac) or if you don’t have an automounter and you are running linux, you can probably figure out how to mount the device as a drive. Drag the U2F file over to this drive. It will disconnected as soon as the transfer completes and the badge should reboot and begin showing some blinky lights!

## Badge Manual

Pressing any of the 9 keys will flash that keyswitch momentarily. Long pressing on one of the 9 keys will change the light themes. The accelerometer will allow you to tilt the badge in any of the light themes to affect the light pattern. Pressing any of the keys while plugged into usb c will output the keystroke 1-9. 

## Troubleshooting

*When i tilt my badge nothing happens?*

Some of the accelerometers may have gotten placed a bit off the pads. Find hamster for help, or if you have a hot air station, mask around the U1? part with kapton tape, and heat it gently while holding it down with some tweezers to realign to the pads. 

*Not all the keys are working?*

Re-check your solder connections on each switch

*The badge caught fire!*

The badge should only be powered by 3x AA batteries or USB-C. Please do not use car batteries, 120V AC, or small nuclear reactors to power the badge.
