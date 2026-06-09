# nagios_prowl_notify

Python script to add [ProwlApp](https://www.prowlapp.com/) push notifications to Nagios.

## About

**Nagios** is an industry-standard open-source monitoring system that watches servers, networks, and applications for problems. When issues occur, Nagios can alert administrators through various notification methods.

**nagios_prowl_notify.py** provides a cheap and easy way to receive Nagios alerts as push notifications on your iOS devices (iPhone, iPod touch, or iPad) through the [Prowl](https://www.prowlapp.com/) service. Push notifications arrive instantly on your device, providing **more immediate notifications than email**, which can be delayed or filtered to spam folders. Push notifications should be used **alongside email** for a comprehensive alerting strategy.

## Why Push Notifications?

Push notifications complement email alerts by offering several advantages:

- **Instant delivery** - Notifications appear immediately on your device's lock screen
- **Always visible** - Harder to miss than emails that can get buried in your inbox
- **Priority levels** - Critical alerts can be set to bypass Do Not Disturb mode
- **Quiet hours** - Configure when you want to receive audible alerts vs. silent badge updates
- **Smart redirections** - Tap a notification to open relevant dashboards or monitoring URLs
- **Battery efficient** - Native iOS push notifications don't drain battery like polling apps

## Prowl Benefits

Using Prowl with Nagios provides:

- **Low cost** - One-time app purchase, no ongoing subscription fees
- **Multi-device support** - Receive alerts on all your iOS devices
- **Flexible priority system** - Emergency alerts can break through Do Not Disturb mode
- **Beautiful interface** - Clean, organized list of notifications
- **Powerful API** - Easy integration with custom monitoring scripts
- **Redundant delivery** - Works alongside email for critical alert redundancy

## Installation & Configuration

See the inline documentation in `nagios_prowl_notify.py` for setup instructions.

The script is configured as a Nagios contact notification command. Your Prowl API key should be stored in the contact's `pager` field.

## References

- [Prowl API Documentation](https://www.prowlapp.com/api.php)
- [Prowl iOS App](https://itunes.apple.com/us/app/prowl-easy-push-notifications/id320876271?mt=8)
- [Nagios Contact Configuration](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/3/en/objectdefinitions.html#contact)
- [Nagios Command Definitions](https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/3/en/objectdefinitions.html#command)
