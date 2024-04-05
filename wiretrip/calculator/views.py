from django.shortcuts import render
import math

ROLL_LENGTH = 90

def home(request):
    return render(request, 'home.html')

def flat(request):
    return render(request, 'calculator/form_flat.html')

def flat_submit(request):

    """
    This function accepts the data submitted by the user for the flat
    and generates results for wire lengths and breaker types + quantity
    """

    if request.method == "POST":

        # create variables to store data
        length = request.POST.getlist('lengths')
        width = request.POST.getlist('widths')
        lu_type = request.POST.getlist('type_of_living_unit')
        connection_type = request.POST.get('type_of_connection')

        # determine breaker type
        if connection_type == 'single_phase':
            main_breaker_type = 'Double Pole (DP)'
        else:
            main_breaker_type = 'Triple Pole (TP)'

        dimensions = []
        breaker_amperage = []

        total_amps = 0

        breaker_counts = {'6A': 0,
                          '10A': 0,
                          '16A': 0,
                          '20A': 0}

        # loop through all living units
        for i in range(len(length)):

            # create a list of living unit dimensions for the floor
            dimensions.append(length[i] + " x " + width[i])

            # number of ACs to calculate number
            # of 20A circuit breakers
            num_acs = int(request.POST.getlist('ACs')[i]) 

            # for outdoor living unit only a 6A circuit breaker
            if lu_type[i] == "Outdoor":
                breaker_amperage.append("1 x 6A")
                total_amps += 6
                breaker_counts['6A'] += 1

            # an additional 20A breaker for every AC
            elif lu_type[i] == "Kitchen":
                
                breaker_amperage.append("1 x 10A and " + str(1+num_acs) + " x 20A")
                total_amps += (10 + (1+num_acs)*20)
                breaker_counts['10A'] += 1
                breaker_counts['20A'] += (1+num_acs)

            # an additional 20A breaker for every AC
            elif num_acs > 0:
                breaker_amperage.append("1 x 10A and " + str(num_acs) + " x 20A")
                total_amps += (10 + num_acs*20)
                breaker_counts['10A'] += 1
                breaker_counts['20A'] += num_acs

            # base condition: a 10A and a 20A breaker for each indoor living unit
            else:
                breaker_amperage.append("1 x 10A and 1 x 20A")
                total_amps += 30
                breaker_counts['10A'] += 1
                breaker_counts['20A'] += 1

        data = {'length_floor':        request.POST.get('length_floor'),
        'width_floor':         request.POST.get('width_floor'),
        'num_living_units':    int(len(length)),
        'lengths':             request.POST.getlist('lengths'),
        'widths':              request.POST.getlist('widths'),
        'type_of_living_unit': request.POST.getlist("type_of_living_unit"),
        'ups_available':       request.POST.get("ups_available")
        }

        # calculate wire lengths
        wire_lengths = calculate_wire_length(data=data)

        # in case of 3-phase reduce total amperage by 30% and divide by 3 
        if connection_type == 'three_phase':
            total_amps = (total_amps - 0.3*total_amps)/3
        else:
            # reduce by 30% in case of single phase
            total_amps = (total_amps - 0.3*total_amps)

        # choosing the nearest breaker based on max current
        if total_amps < 40:
            main_breaker_rating = 30
        elif total_amps < 50:
            main_breaker_rating = 40
        elif total_amps < 60:
            main_breaker_rating = 50
        elif total_amps < 100:
            main_breaker_rating = 60
        else:
            main_breaker_rating = 100
        
        breaker_counts[str(main_breaker_rating) + "A " + main_breaker_type] = 1

        # creating lists to store breaker types and quantities
        types = []
        quantity = []
        for k in breaker_counts.keys():
            if breaker_counts.get(k) > 0:
                types.append(k)
                quantity.append(breaker_counts.get(k))

        # dictionary containing data for table 2 on results page
        table_2 = [{'item1': t[0], 'item2': t[1], 'item3':t[2]} for t in zip(lu_type, dimensions, breaker_amperage)]

        # dictionary containing data for table 3 on results page
        table_3 = [{'item1': t[0], 'item2': t[1]} for t in zip(types, quantity)]

        return render(request, 'calculator/results_flat.html', {'length_main': wire_lengths.get('primary'),
                                                                'length_sec_red': wire_lengths.get('secondary_red'),
                                                                'length_sec_black': wire_lengths.get('secondary_black'),
                                                                'num_rolls_main': wire_lengths.get('num_rolls_primary'),
                                                                'num_rolls_sec_red': wire_lengths.get('num_rolls_secondary_red'),
                                                                'num_rolls_sec_black': wire_lengths.get('num_rolls_secondary_black'),
                                                                'rows_table_2': table_2,
                                                                'rows_table_3': table_3})

def house(request):
    return render(request, 'calculator/form_house.html')

def house_submit(request):

    """
    This function accepts the data from the form and makes calculations
    for wire lengths and breaker type and quantity and passes the results 
    to a results page.
    """

    if request.method == "POST":

        # store data in separate variables
        floor_names = request.POST.getlist('floor_name')
        num_floors = len(floor_names)
        length_floor = [int(x) for x in request.POST.getlist('length_floor')]
        width_floor = [int(x) for x in request.POST.getlist('width_floor')]
        num_living_units = [int(x) for x in request.POST.getlist('num_living_units')]
        connection_type = request.POST.getlist('type_of_connection')
        ups_provision = request.POST.getlist('ups_available')

        lu_type = request.POST.getlist('type_of_living_unit')
        length = request.POST.getlist('lengths')
        width = request.POST.getlist('widths')

        ACs = request.POST.getlist('ACs')
        refrigerators = request.POST.getlist('refrigerators')
        ovens = request.POST.getlist('ovens')
        hv_switch_boards = request.POST.getlist('hv_switch_boards')

        floors = []

        # loop through all floors
        for i in range(num_floors):

            floor = {}

            # create a dictionary "floors" with the floor properties
            floor['name'] = floor_names[i]
            floor['connection'] = connection_type[i]
            floor['ups_provision'] = ups_provision[i]
            floor['length'] = int(length_floor[i])
            floor['width'] = int(width_floor[i])
            floor['num_lu'] = int(num_living_units[i])

            N = floor.get("num_lu")

            floor["living_unit_lengths"] = length[:N]
            floor["living_unit_widths"] = width[:N]
            floor["living_unit_types"] = lu_type[:N]

            # determine main DB breaker type
            if floor.get("connection") == 'single_phase':
                main_breaker_type = 'Double Pole (DP)'
            else:
                main_breaker_type = 'Triple Pole (TP)'

            dimensions = []
            breaker_amperage = []

            total_amps = 0

            # use a dictionary to count number of each breaker
            breaker_counts = {'6A': 0, '10A': 0,
                            '16A': 0, '20A': 0}


            # only take values for the current floor using the number 
            # of living units
            floor_ACs = ACs[:N]
            floor_refrigerators = refrigerators[:N]
            floor_ovens = ovens[:N]
            floor_hv_boards = hv_switch_boards[:N]

            # create a list of living unit dimensions for the floor
            for i in range(N):
                dimensions.append(floor.get("living_unit_lengths")[i] + " x " + floor.get("living_unit_widths")[i])
                
                # number of ACs to calculate number
                # of 20A circuit breakers
                num_acs = int(floor_ACs[i])   

                # for outdoor living unit only a 6A circuit breaker
                if floor.get("living_unit_types")[i] == "Outdoor":
                    breaker_amperage.append("1 x 6A")
                    total_amps += 6
                    breaker_counts['6A'] += 1

                # kitchen will have one 20 A breaker for all kitchen-related 
                # appliances and on2 breaker for every AC
                elif floor.get("living_unit_types")[i] == "Kitchen":
                    breaker_amperage.append("1 x 10A and " + str(1+num_acs) + " x 20A")
                    total_amps += (10 + (1+num_acs)*20)
                    breaker_counts['10A'] += 1
                    breaker_counts['20A'] += (1+num_acs)

                # an additional 20A breaker for each HV appliance
                elif num_acs > 0:
                    breaker_amperage.append("1 x 10A and " + str(num_acs) + " x 20A")
                    total_amps += (10 + num_acs*20)
                    breaker_counts['10A'] += 1
                    breaker_counts['20A'] += num_acs

                # base condition: a 10A and a 20A breaker for each indoor living unit
                else:
                    breaker_amperage.append("1 x 10A and 1 x 20A")
                    total_amps += 30
                    breaker_counts['10A'] += 1
                    breaker_counts['20A'] += 1

            # data used for wire calculations
            data = {'length_floor':        floor.get('length'),
                    'width_floor':         floor.get('width'),
                    'num_living_units':    floor.get('num_lu'),
                    'lengths':             floor.get('living_unit_lengths'),
                    'widths':              floor.get('living_unit_widths'),
                    'type_of_living_unit': floor.get("living_unit_types"),
                    'ups_available':       floor.get("ups_provision")
                    }

            # calculate wire lengths
            wire_lengths = calculate_wire_length(data=data)

            # in case of 3-phase reduce total amperage by 30% and divide by 3 
            if floor.get("connection") == 'three_phase':
                total_amps = (total_amps - 0.3*total_amps)/3
            else:
                # reduce by 30% in case of single phase
                total_amps = (total_amps - 0.3*total_amps)

            # choosing the nearest breaker based on max current
            if total_amps < 40:
                main_breaker_rating = 30
            elif total_amps < 50:
                main_breaker_rating = 40
            elif total_amps < 60:
                main_breaker_rating = 50
            elif total_amps < 100:
                main_breaker_rating = 60
            else:
                main_breaker_rating = 100
            
            breaker_counts[str(main_breaker_rating) + "A " + main_breaker_type] = 1

            # creating lists to store breaker types and quantities
            types = []
            quantity = []
            for k in breaker_counts.keys():
                if breaker_counts.get(k) > 0:
                    types.append(k)
                    quantity.append(breaker_counts.get(k))

            # dictionary containing data for table 2 on results page
            table_2 = [{'item1': t[0], 'item2': t[1], 'item3':t[2]} for t in zip(floor.get("living_unit_types"), dimensions, breaker_amperage)]
            
            # dictionary containing data for table 3 on results page
            table_3 = [{'item1': t[0], 'item2': t[1]} for t in zip(types, quantity)]

            floor['rows_table_2'] = table_2
            floor['rows_table_3'] = table_3

            # remove items for the floor
            length = length[N:]
            width = width[N:]
            ACs = ACs[N:]
            refrigerators = refrigerators[N:]
            ovens = ovens[N:]
            hv_switch_boards = hv_switch_boards[N:]
            lu_type = lu_type[N:]

            floor['length_main'] =  wire_lengths.get('primary')
            floor['length_sec_red'] = wire_lengths.get('secondary_red')
            floor['length_sec_black'] = wire_lengths.get('secondary_black')

            floor['num_rolls_main'] =  wire_lengths.get('num_rolls_primary')
            floor['num_rolls_sec_red'] = wire_lengths.get('num_rolls_secondary_red')
            floor['num_rolls_sec_black'] = wire_lengths.get('num_rolls_secondary_black')

            floors.append(floor)

        return render(request, 'calculator/results_house.html', {'floors': floors})

def calculate_wire_length(data):
    
    """
    function to calculate wire lengths (in number of 90m rolls)
    for primary and secondary circuits in the building.

    """
    # create variables to store data
    length_floor = int(data.get('length_floor'))
    width_floor = int(data.get('width_floor'))
    num_living_units = int(data.get('num_living_units'))
    length = data.get('lengths')
    width = data.get('widths')
    lu_type = data.get('type_of_living_unit')

    # initialize length of the primary wires
    # 2.5 mm, 4/6 mm, and earth
    len_primary = 0

    # initialize length of the secondary wires
    # 1.5 mm
    len_secondary_red   = 0
    len_secondary_black = 0

    # sum the max dimension of each living unit
    for i in range(num_living_units):
        len_primary += max([int(length[i]), int(width[i])])

    # if the sum of max dimension for each living unit is less than
    # sum of floor dimensions, consider the sum of floor dimensions
    # as the length of the primary circuit.

    if len_primary < (length_floor + width_floor):
        len_primary = length_floor + width_floor

    # add a secondary circuit for each living unit
    for i in range(num_living_units):

        # for outdoor living units 
        if lu_type[i] == "Outdoor":
            len_secondary_red   += 2 * 90 * 3.281
            len_secondary_black += 1 * 90 * 3.281

        # for indoor living units    
        else:

            # calculate square footage 
            area = int(length[i])*int(width[i])

            # assign secondary circuit wire based on square footage
            if area < 150:
                len_secondary_red   += 1 * ROLL_LENGTH * 3.281
                len_secondary_black += 1 * ROLL_LENGTH * 3.281
            elif area < 300:
                len_secondary_red   += 2 * ROLL_LENGTH * 3.281
                len_secondary_black += 1 * ROLL_LENGTH * 3.281
            else:
                len_secondary_red   += 3 * ROLL_LENGTH * 3.281
                len_secondary_black += 1 * ROLL_LENGTH * 3.281

        # add 30% to 1.5 mm wire in case of UPS
        if data.get('ups_available') == "yes":
            len_secondary_black += 0.3*len_secondary_black
            len_secondary_red += 0.3*len_secondary_red

        # convert to meters
        len_primary = math.ceil(3*len_primary/3.281) 
        len_secondary_black = math.ceil(len_secondary_black/3.281)
        len_secondary_red = math.ceil(len_secondary_red/3.281)

        # convert to nearest length in number of rolls
        rolls_primary = math.ceil(len_primary/ROLL_LENGTH)
        rolls_secondary_red = math.ceil(len_secondary_red/ROLL_LENGTH)
        rolls_secondary_black = math.ceil(len_secondary_black/ROLL_LENGTH)

        return {'primary': len_primary, 
                'secondary_red': len_secondary_red,
                'secondary_black': len_secondary_black,
                'num_rolls_primary': rolls_primary, 
                'num_rolls_secondary_red': rolls_secondary_red,
                'num_rolls_secondary_black': rolls_secondary_black,}
