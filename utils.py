def time_check(end, time):
    if end in 'мm':
        if time in (1, 21, 31, 41, 51):
            ending = 'минуту'
        elif time in (2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54):
            ending = 'минуты'
        else:
            ending = 'минут'
    elif end in 'hч':
        if time in (1, 21):
            ending = 'час'
        elif time in (2, 3, 4, 22, 23, 24):
            ending = 'часа'
        else:
            ending = 'часов'
    return ending

def wedding_date_now(date):
    duration = date
    day_time = 60*60*24
    hours = 60*60
    minutes = 60
    day = int(duration//day_time)
    hour = int(duration%day_time//hours)
    minute = int(duration%day_time%hours//minutes)
    seconds = int(duration%day_time%hours%minutes)
    return f'{day} д. {hour} ч. {minute} мин. {seconds} сек'
