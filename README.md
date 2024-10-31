# `sfs`

SMU FBS scraper.

```console
$ make config
$ make
```

## How to build

Don't.  
  
Access the telegram bot [`smu_fbs_scraper_bot`](https://t.me/smu_fbs_scraper_bot).

## Actually how build

### Secret

`credentials.json` must follow the below format.

```json
{
    "username": "fill_your_placeholder_username",
    "password": "fill_your_placeholder_password"
}
```

### Scraping

Scraping returns `scraped_log.json`, which contains the following.

* Scraping metadata

```json
"metrics": {
    "scraping_date": "current_date"
},
```

* Scraping configuration

```json
"config": {
    "date": "specified_date",
    "start_time": "specified_start_time",
    "end_time": "specified_end_time",
    "duration": 0, /* any integer value */
    "building_names": [
        "specified_schools"
    ],
    "floors": [
        "specified_floors"
    ],
    "facility_types": [
        "specified_facility_types"
    ],
    "room_capacity": 0, /* any integer value */
    "equipment": [
        "specified_equipment"
    ]
},
```

* Scraped results

```json
"result": {
    "room_1": [
        {
            "timeslot": "timeslot_1",
            "available": false,
            "status": "Not available",
            "details": null
        },
        {
            "timeslot": "timeslot_2",
            "available": false,
            "status": "Booked",
            "details": {
                "Booking Time": "...",
                "Booking Status": "...",
                "Booking Reference Number": "...",
                "Booked for User Name": "...",
                "Booked for User Org Unit": "",
                "Booked for User Email Address": "...",
                "Use Type": "...",
                "Purpose of Booking": "..."
            }
        }
    ],
    "room_2": [
        /* ... */
    ],
    /* ... */
}
```

## Contributors

<table>
	<tbody>
        <tr>
            <td align="center">
                <a href="https://github.com/SpringOrca69">
                    <img src="https://avatars.githubusercontent.com/u/159885540?v=4" width="100;" alt="SpringOrca69"/>
                    <br />
                    <sub><b>SpringOrca69</b></sub>
                </a>
            </td>
	</tr>
	<tbody>
</table>
