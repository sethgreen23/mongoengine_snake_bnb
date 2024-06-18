from infrastructure.switchlang import switch
import program_hosts as hosts
import infrastructure.state as state
from program_hosts import error_msg, success_msg
import services.data_service as svc
from dateutil.parser import parse
import datetime
import inspect

def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)
            s.case('l', hosts.log_into_account)

            s.case('a', add_a_snake)
            s.case('y', view_your_snakes)
            s.case('b', book_a_cage)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a cage')
    print('[A]dd a snake')
    print('View [y]our snakes')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_snake():
    print(' ****************** Add a snake **************** ')
    # TODO: Require an account
    # TODO: Get snake info from user
    # TODO: Create the snake in the DB.

    if not state.active_account:
        error_msg('ERROR: You must be logged in to add a snake. ')
        return
    name = input("What is the snake's name? ")
    if not name:
        error_msg('Canceled. ')
        return
    
    length = float(input("What is the snake's length (in meters)? "))
    species = input("Species: ")
    is_venemous = input("Veneomous [y/n] ").lower().startswith('y')
    snake = svc.add_snake(state.active_account, name, length, species, is_venemous)
    state.reload_account()
    success_msg(f'Snake {snake.name} with id {snake.id} added successfully!')


def view_your_snakes():
    print(' ****************** Your snakes **************** ')

    # TODO: Require an account
    # TODO: Get snakes from DB, show details list

    if not state.active_account:
        error_msg('ERROR: You must be logged in to view your snakes. ')
        return
    
    snakes = svc.get_snakes_for_owner(state.active_account.id)
    print("You have {} snakes.".format(len(snakes)))
    for s in snakes:
        print("	* {} is a {} that is {}m long and is {}venemous.".format(
			s.name,
			s.species,
			s.length,
			'' if s.is_venomous else 'NOT '
		))


def book_a_cage():
    print(' ****************** Book a cage **************** ')
    # TODO: Require an account
    # TODO: Verify they have a snake
    # TODO: Get dates and select snake
    # TODO: Find cages available across date range
    # TODO: Let user select cage to book.
    
    if not state.active_account:
        error_msg("You must log in first to book a cage")
        return
    
    snakes = svc.get_snakes_for_owner(state.active_account.id)
    if not snakes:
        error_msg('You must first [a]dd a snake. before you can book a cage')
        return
    
    print("Let's start by finding available cages.")
    start_text = input("Check-in date [yyyy-mm-dd]: ")
    if not start_text:
        error_msg('Canceled. ')
        return
    
    checkin = parse(start_text)
    checkout = parse(input("Check-out date [yyyy-mm-dd]: "))
    if checkin >= checkout:
        error_msg('Check-out date must be after check-in date. ')
        return
    
    print()
    for idx, s in enumerate(snakes):
        print('{} {} (length: {}, venomous: {})'.format(
			idx + 1,
			s.name,
			s.length,
			'yes' if s.is_venomous else 'no'
		))
    snake = snakes[int(input('Which snake would you like to book? ')) - 1]
    cages = svc.get_available_cages(checkin, checkout, snake)
    print("There are {} cages available.".format(len(cages)))
    for idx, c in enumerate(cages):
        print(" {}. {}  with {}m carpeted: {}, has toys: {}.".format(
			idx + 1,
			c.name,
			c.square_meters,
			'yes' if c.is_carpeted else 'no',
			'yes' if c.has_toys else 'no'
		))
    
    if not cages:
        error_msg('No available cages. ')
        return
    
    cage = cages[int(input("which cage would you like to book? ")) - 1]
    svc.book_cage(state.active_account,snake, cage, checkin, checkout)
    success_msg('Successfully booked {} for {} at {}/night'.format(cage.name, snake.name, cage.price))
    



def view_bookings():
    print(' ****************** Your bookings **************** ')
    # TODO: Require an account
    # TODO: List booking info along with snake info

    if not state.active_account:
        error_msg('ERROR: You must be logged in to view your bookings. ')
        return
    
    snakes = {s.id: s for s in svc.get_snakes_for_owner(state.active_account.id)}
    bookings = svc.get_bookings_for_owner(state.active_account.email)
    print("You have {} bookings.".format(len(bookings)))
    for b in bookings:
        print('	* Snake: {} is booked at {} from {} for {} days'.format(
			snakes[b.guest_snake_id].name,
			b.cage.name,
			datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
			(b.check_out_date - b.check_in_date).days
		))
