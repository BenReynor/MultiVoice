#!/bin/bash
# Start the virtual microphone for Discord

pactl unload-module module-null-sink 2>/dev/null
pactl unload-module module-loopback 2>/dev/null
pactl unload-module module-remap-source 2>/dev/null
pactl unload-module module-always-sink 2>/dev/null
sleep 1

pactl load-module module-null-sink sink_name=virtual-sink sink_properties=device.master_volume=1.0,sink_dont_move=yes sample_spec=s16le=2ch=48000Hz
pactl load-module module-remap-source source_name=virtual-mic master=virtual-sink.monitor source_properties=device.description="🎤"

pactl set-default-sink alsa_output.usb-Generic_USB_Audio_Device_20210726905926-00.analog-stereo
pactl set-default-source alsa_input.usb-Generic_USB_Audio_Device_20210726905926-00.mono-fallback

echo "✅ Virtual mic ready: '🎤'"