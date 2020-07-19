# Home Assistant Security Feed
A custom component to review a feed of security images in Home Assistant.

See [this page](https://www.technicallywizardry.com/diy-home-security-camera/) for example usage and more details.

* View images from a given folder
* Alert when new images appear in the folder
* Delete or save each image

![Security Feed](https://content.technicallywizardry.com/2020/07/19174345/ha-security-feed-recording.png)

In the above screenshot, there are no images for review. When an image appears in the folder, it is shown in the card. The trash button deletes the image, while the save button also copies it to a storage folder first.

## Installation

You can use HACS. Otherwise, download the latest Release and place all the python files in `/config/custom_components/security_feed` (and then restart Home Assistant). You should also place `security_feed_empty.jpg` in the `/config/www/` folder (unless you prefer to use your own image).

## Files for Review

As explained [here](https://www.technicallywizardry.com/diy-home-security-camera/), the images for review should be tagged by some object detection service. The files should have the following name format: `2020-07-18_13-59-12_doorbell_truck_64.jpg`. Separated by underscores, the four parts of the name are:

* Timestamp
* Location
* Tag
* Confidence %

So for the above example, the object detection system was 64% confident it saw a truck at the doorbell.

## Configuration

Example: detect `jpg` files in `/config/www/security_feed`. Saved files will be moved to `/cctv-storage`.

```
sensor:
  - platform: security_feed
    name: motion_detections
    folder: "/config/www/security_feed"
    filter: "*.jpg"
    storage: "/cctv-storage"
```

Optionally, you can set `www` to the path for your `www` directory (default is `/config/www/`). You can also set `empty_image` to the path for the empty-state image (default is `/config/www/security_feed_empty.jpg`).

## Events

The entity supports the `security_feed` event, with the arguments `entity_id` (i.e., `security_feed.motion_detections`) and `save` set to true or false. You can wrap this with a script:

```
script:
  security_feed:
    alias: Process Security Feed
    sequence:
    - event: security_feed
      event_data_template:
        entity_id: "{{ entity_id }}"
        save: "{{ save }}"
```

## Lovelace (UI)

I used the [Config Template Card](https://github.com/iantrich/config-template-card) to create a card for my feed:

```
card:
  entities:
    - entity: security_feed.motion_detections
      icon: 'mdi:delete'
      tap_action:
        action: call-service
        service: script.security_feed
        service_data:
          action: delete
          entity_id: security_feed.motion_detections
    - entity: security_feed.motion_detections
      icon: 'mdi:content-save'
      tap_action:
        action: call-service
        service: script.security_feed
        service_data:
          action: save
          entity_id: security_feed.motion_detections
  entity: security_feed.motion_detections
  image: '${vars[0]}'
  title: '${vars[1]}'
  type: picture-glance
entities:
  - security_feed.motion_detections
type: 'custom:config-template-card'
variables:
  - 'states[''security_feed.motion_detections''].attributes.entity_picture'
  - 'states[''security_feed.motion_detections''].attributes.friendly_name'
```
