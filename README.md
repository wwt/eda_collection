# Event Driven Automation Collection - wwt.eda

The goal of this collection is to provide a variety of event-source plugins and filters for Event-Driven Ansible.

## Plugins

The following plugins are included in the collection

| Name | Description |
|-|-|
| wwt.eda.mqtt | MQTT Event Source Plugin |
| wwt.eda.bigpanda | Big Panda Event Source Plugin |

### wwt.eda.mqtt plugin

This plugin was originally based off of the work done by Alessandro Rossi (<https://github.com/kubealex>) and his MQTT event-source plugin.

### wwt.eda.bigpanda

This is a new plugin to integrate with Big Panda and collect incidents as a source for event-driven ansible.

## Python Dependencies

See `requirements.txt` for python dependencies.

## Usage

### wwt.eda.mqtt Usage

A sample rulebook using *wwt.eda.mqtt* plugin is shown below:

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

### wwt.eda.bigpanda Usage

A sample rulebook using *wwt.eda.bigpanda* plugin is shown below:

```yaml
---
- name: Remediate WWT-Demo Application
  hosts: all
  sources:
    - wwt.eda.bigpanda:
        api_token: <big-panda-api-token>
        environment: <big-panda-environment-name>
        delay: 10
  rules:
    - name: Restart Demo Application
      condition: >-
        event.alert.tags.alertname == "MainPageHTTPStatusNotOK" and
        event.alert.tags.event_action == "recreate"
      throttle:
        once_within: 5 minutes
        group_by_attributes:
          - event.incident.id
      action:
        run_job_template:
          name: Restart Demo App
          organization: Application-Demo
          job_args:
            extra_vars:
              deployment_name: "{{ event.alert.tags.container }}"
              k8s_namespace: "{{ event.alert.tags.app }}"
```
