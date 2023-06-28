# Event Driven Automation Collection - wwt.eda

This collection is originally based off of the work done by Alessandro Rossi (<https://github.com/kubealex>).

The goal of this collection is to provide a variety of event-source plugins and filters for Event-Driven Ansible.

## Plugins

The following plugins are included in the collection

| Name | Description |
|-|-|
| wwt.eda.mqtt | MQTT Event Source Plugin |

## Usage

A sample rulebook using *wwt.eda.mqtt* plugin is shown below

```yaml
---
- name: Meraki MT30 Sensor Button Presses
  hosts: all
  sources:
    - wwt.eda.mqtt:
        host: <host>
        port: 8883
        username: <username>
        password: <password>
        ca_certs: <path/to/cert>
        validate_certs: false
        topic: meraki/v1/mt/#
      filters:
        - compare_mqtt_timestamp:
  rules:
    - name: Button Long Press
      condition: event.action == "longPress" and event.timestamps.msg_age < 10
      action:
        run_job_template:
          name: Unconfigure Demo Environment
          organization: Meraki-Demo
    - name: Button Short Press
      condition: event.action == "shortPress" and event.timestamps.msg_age < 10
      action:
        run_job_template:
          name: Send Webex Teams Message
          organization: Meraki-Demo
          job_args:
            extra_vars:
              source_device: "demo-mt30"
              camera_name: "demo-mv2"
              webex_room_name: "WWT Ansible EDA Demo"
```
