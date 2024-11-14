import os
import json
import aiofiles
from dateutil.parser import parse
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from exceptions import FrameNotFoundException

def generate_30_min_intervals():
    intervals = []
    start = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:59", "%H:%M")
    while start <= end:
        interval_end = (start + timedelta(minutes=30)).strftime("%H:%M")
        intervals.append(f"{start.strftime('%H:%M')}-{interval_end}")
        start += timedelta(minutes=30)
    return intervals

def remove_duplicates_preserve_order(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def fill_missing_timeslots(room_schedule, target_timeslot_array):
    new_schedule = []
    for slot in room_schedule:
        if slot["timeslot"] == target_timeslot_array[0]:  # already exists
            new_schedule.append(slot)
            del target_timeslot_array[0]
        else:  # does not yet exist
            new_timeslot = target_timeslot_array.pop(0)
            new_schedule.append({
                "timeslot": new_timeslot,
                "available": True,
                "status": "Available for booking",
                "details": None
            })
            new_schedule.append(slot)  # Insert the existing slot
            del target_timeslot_array[0]
    return new_schedule

def pretty_print_json(json_object):
    print(json.dumps(json_object, indent=4)) 

async def write_json(json_object, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    async with aiofiles.open(filename, 'w') as json_file:
        await json_file.write(json.dumps(json_object, indent=4))
    print(f"JSON file written to filepath: {filename}")

async def convert_room_capacity(room_capacity_raw, capacity_mapping):
    for condition, value in capacity_mapping.items():
        if condition(room_capacity_raw):
            return value
    return "MoreThan100Pax"

def calculate_end_time(valid_time_array, start_time, duration_hrs):
    start_hours, start_minutes = map(int, start_time.split(":"))
    total_minutes = (start_hours * 60 + start_minutes) + int(duration_hrs * 60)
    end_hours = (total_minutes // 60) % 24
    end_minutes = total_minutes % 60
    end_time = f"{end_hours:02}:{end_minutes:02}"
    closest_time = min(valid_time_array, key=lambda t: abs((int(t.split(":")[0]) * 60 + int(t.split(":")[1])) - (end_hours * 60 + end_minutes)))
    return [closest_time, end_time]

from dateutil.parser import parse
from datetime import datetime

def format_date(date_input):
    try:
        date_obj = parse(date_input)
        today = datetime.now().date()
        if date_obj.date() < today:
            raise ValueError(f"The input date {date_obj.strftime('%d-%b-%Y')} is in the past.")
        
        return date_obj.strftime("%d-%b-%Y")
    
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date input: {e}")


def split_bookings_by_day(bookings):
    days = []
    current_day = []
    for booking in bookings:
        if '(not available)' in booking:
            if not current_day:
                current_day.append(booking)
            else:
                current_day.append(booking)
                days.append(current_day)
                current_day = [] 
        else:
            if current_day:
                current_day.append(booking)
    return days

def add_missing_timeslots(booking_details, target_timeslot_array):
    complete_booking_details = []
    for timeslot in target_timeslot_array:
        found = False
        for booking in booking_details:
            if booking["timeslot"] == timeslot:
                complete_booking_details.append(booking)
                found = True
                break
        if not found:
            complete_booking_details.append({
                "timeslot": timeslot,
                "available": True,
                "status": "Unbooked",
                "details": None
            })
    return complete_booking_details

### SCRAPING METHODS ####
async def login_credentials(page, constants, local_credentials):
    await page.goto(constants['target_url'])
    print(f"Navigating to {constants['target_url']}")

    selectors = ['input#userNameInput', 'input#passwordInput', 'span#submitButton']
    for selector in selectors:
        await page.wait_for_selector(selector)

    await page.fill("input#userNameInput", local_credentials.username)
    await page.fill("input#passwordInput", local_credentials.password)
    await page.click("span#submitButton")

    await page.wait_for_timeout(6000)
    await page.wait_for_load_state('networkidle')


async def select_dropdown_options(frame, dropdown_selector, options, hide_popup_js="popup.hide()"):
    if not options:
        return

    if await frame.is_visible(dropdown_selector):
        await frame.click(dropdown_selector)  # Opens the dropdown list
        for option in options:
            await frame.click(f'text="{option}"')
            print(f"Selecting {option}...")
        await frame.evaluate(hide_popup_js)  # Closes the dropdown list
        await frame.page.wait_for_load_state('networkidle')
        await frame.wait_for_timeout(3000)


async def apply_filters(frame, request):
    HIDE_POPUP = "popup.hide()"
    await select_dropdown_options(frame, '#DropMultiBuildingList_c1_textItem', request.building_names, HIDE_POPUP)
    await select_dropdown_options(frame, '#DropMultiFloorList_c1_textItem', request.floors, HIDE_POPUP)
    await select_dropdown_options(frame, '#DropMultiFacilityTypeList_c1_textItem', request.facility_types, HIDE_POPUP)
    await select_dropdown_options(frame, '#DropMultiEquipmentList_c1_textItem', request.equipment, HIDE_POPUP)


async def select_time(frame, time_selector, time_value, description):
    select_input = await frame.query_selector(time_selector)
    if select_input:
        await frame.evaluate(f'document.querySelector("{time_selector}").value = "{time_value}"')
        print(f"Selected {description} to be {time_value}")
    else:
        print(f"Select element for {description.lower()} not found")


async def navigate_to_date(frame, target_date):
    while True:
        current_date_element = await frame.query_selector("input#DateBookingFrom_c1_textDate")
        current_date_value = await current_date_element.get_attribute("value")
        if current_date_value == target_date:
            print(f"Final day is {current_date_value}")
            break
        else:
            print(f"Current day is {current_date_value}")
            print("Navigating to the next day...")
            await frame.click("a#BtnDpcNext.btn")
            await frame.wait_for_timeout(1500)


async def extract_matching_rooms(frame):
    await frame.wait_for_selector("table#GridResults_gv")
    matching_rooms = []
    rows = await frame.query_selector_all("table#GridResults_gv tbody tr")
    for row in rows:
        tds = await row.query_selector_all("td")
        if len(tds) > 1:
            room_text = (await tds[1].inner_text()).strip()
            matching_rooms.append(room_text)
    return matching_rooms

async def scrape_timeslots(frame, valid_buildings):
    room_names_raw = [await room.inner_text() for room in await frame.query_selector_all("div.scheduler_bluewhite_rowheader_inner")]
    room_names = [name for name in room_names_raw if name not in valid_buildings]
    
    bookings_elements = await frame.query_selector_all("div.scheduler_bluewhite_event.scheduler_bluewhite_event_line0")
    bookings_raw = [await elem.get_attribute("title") for elem in bookings_elements]
    bookings_sanitised = split_bookings_by_day(bookings_raw)
    
    room_timeslot_map = {}
    for index, booking_array in enumerate(bookings_sanitised):
        booking_details = []
        for booking in booking_array:
            if booking.startswith("Booking Time:"):
                details = {}
                lines = booking.split("\n")
                timeslot = lines[0].replace("Booking Time: ", "")
                for line in lines[1:]:
                    key, value = line.split(": ", 1)
                    details[key] = value
                booking_details.append({
                    "timeslot": timeslot,
                    "available": False,
                    "status": "Booked",
                    "details": details
                })
            elif booking.endswith("(not available)"):
                time = booking.split(") (")[0].lstrip("(")
                booking_details.append({
                    "timeslot": time,
                    "available": False,
                    "status": "Not available",
                    "details": None
                })
            else:
                print(f"Unrecognised timeslot format, logged here: {booking}")

        room_timeslot_map[room_names[index]] = fill_missing_timeslots(booking_details, generate_30_min_intervals())
    
    return room_timeslot_map


async def scrape_smu_fbs(request, constants):
    """
    Asynchronously handle automated login to SMU FBS and scrape booked timeslots.
    Returns the final booking log.
    """
    try:
        DATE_FORMATTED = format_date(request.date_raw)
        END_TIME = calculate_end_time(constants['valid_time'], request.start_time, request.duration_hours)[0]
        ROOM_CAPACITY_FORMATTED = await convert_room_capacity(7, {
            lambda x: x < 5: "LessThan5Pax",
            lambda x: x <= 10: "From6To10Pax",
            lambda x: x <= 15: "From11To15Pax",
            lambda x: x <= 20: "From16To20Pax",
            lambda x: x <= 50: "From21To50Pax",
            lambda x: x <= 100: "From51To100Pax",
        })
        
        # Ensure directories exist
        os.makedirs(constants['screenshot_filepath'], exist_ok=True)
        os.makedirs(constants['booking_log_filepath'], exist_ok=True)
        
        local_credentials = request.credentials
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=1000)
            page = await browser.new_page()
            
            try:
                # Login
                await login_credentials(page, constants, local_credentials)
                
                # Navigate to content frame
                frame = page.frame(name="frameContent")
                if not frame:
                    raise FrameNotFoundException("Frame 'frameContent' could not be found.")
                
                # Navigate to the desired date
                await navigate_to_date(frame, DATE_FORMATTED)
                
                # Select start and end times
                await select_time(frame, "select#TimeFrom_c1_ctl04", request.start_time, "start time")
                await select_time(frame, "select#TimeTo_c1_ctl04", END_TIME, "end time")
                await frame.wait_for_timeout(3000)
                
                # Apply filters
                await apply_filters(frame, request)
                
                # Select room capacity
                await select_time(frame, "select#DropCapacity_c1", ROOM_CAPACITY_FORMATTED, "room capacity")
                await frame.wait_for_timeout(3000)
                
                # Take initial screenshot
                await page.screenshot(path=os.path.join(constants['screenshot_filepath'], "0.png"))
                
                # Extract matching rooms
                matching_rooms = await extract_matching_rooms(frame)
                if not matching_rooms:
                    print("No rooms fitting description found.")
                    return await generate_final_log(constants, DATE_FORMATTED, request, {})
                
                print(f"{len(matching_rooms)} rooms fitting description found:")
                for room in matching_rooms:
                    print(f"- {room}")
                
                # Search availability
                await frame.click("a#CheckAvailability")
                print("Submitting search availability request...")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(6000)
                
                # Capture screenshot of timeslots
                await page.screenshot(path=os.path.join(constants['screenshot_filepath'], "1.png"))
                
                # Scrape timeslots
                final_timeslot_map = await scrape_timeslots(frame, constants['valid_buildings'])
                
                # Generate and write final booking log
                return await generate_final_log(constants, DATE_FORMATTED, request, final_timeslot_map)
            
            except FrameNotFoundException as fnf_error:
                print(f"Frame not found error: {fnf_error}")
                raise fnf_error
            
            except Exception as e:
                print(f"Error processing {constants['target_url']}: {e}")
                raise e
            
            finally:
                print("Closing browser...")
                await browser.close()
    
    except Exception as e:
        print(f"Failed to initialize Playwright: {e}")
        raise e


async def generate_final_log(constants, date_formatted, request, result):
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_booking_log = {
        "metrics": {
            "scraping_date": current_datetime,
        },
        "scraped": {
            "config": {
                "date": date_formatted,
                "start_time": request.start_time,
                "end_time": calculate_end_time(constants['valid_time'], request.start_time, request.duration_hours)[0],
                "duration": request.duration_hours,
                "building_names": request.building_names,
                "floors": request.floors,
                "facility_types": request.facility_types,
                "room_capacity": await convert_room_capacity(7, {
                    lambda x: x < 5: "LessThan5Pax",
                    lambda x: x <= 10: "From6To10Pax",
                    lambda x: x <= 15: "From11To15Pax",
                    lambda x: x <= 20: "From16To20Pax",
                    lambda x: x <= 50: "From21To50Pax",
                    lambda x: x <= 100: "From51To100Pax",
                }),
                "equipment": request.equipment
            },
            "result": result
        }
    }
    await write_json(final_booking_log, os.path.join(constants['booking_log_filepath'], "scraped_log.json"))
    return final_booking_log

