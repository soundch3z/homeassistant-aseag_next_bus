# ASEAG Next Bus sensor for Home Assistant

Custom [Home Assistant](https://www.home-assistant.io) component to retrieve next bus information from the ASEAG

-stop_ids from the [OpenData portal](http://opendata.avv.de/) are supported now.
-compatible with HACS

## Configuration example:
~~~
sensor:
  - platform: aseag_next_bus
    name: aseag_next_bus
    mode: list
    stop_id: 1001
    tracks:
      - track: 'H.1'
      - track: 'H.2'
  - platform: aseag_next_bus
    name: aseag_next_bus
    mode: single
    stop_id: 1001
    track: 'H.1'
  - platform: aseag_next_bus
    name: aseag_next_bus
    mode: list
    stop_id: 1001
~~~
When no track is specified all tracks will be used
