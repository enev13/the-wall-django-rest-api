YARDS_ICE_PER_FOOT = 195
GOLD_PER_YARD_ICE = 1900


def calculate_ice_amount(sections_string):
    sections = map(int, sections_string.split(" "))
    return_amount = []
    for _ in range(30):
        amt_per_day = 0
        for i in range(len(sections)):
            if sections[i] < 30:
                sections[i] += 1
                amt_per_day += 1
        return_amount.append(amt_per_day)
    return return_amount * YARDS_ICE_PER_FOOT


def calculate_cost(ice):
    return ice * GOLD_PER_YARD_ICE
