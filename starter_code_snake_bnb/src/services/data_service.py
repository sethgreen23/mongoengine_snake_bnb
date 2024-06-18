from data.owners import Owner
from data.cages import Cage
from data.snakes import Snake
from data.bookings import Booking
import datetime
import bson

from typing import List

def create_account(name: str, email: str) -> Owner:
    owner = Owner()
    owner.name = name
    owner.email = email
    
    owner.save()
    
    return owner


def find_account_by_email(email: str) -> Owner:
    owner = Owner.objects().filter(email=email).first()
    return owner


def register_cage(
    owner: Owner, name: str,
    meters: float,
    carpeted: bool,
    has_toys: bool,
    allow_dangerous: bool,
    price: float = None) -> Cage:
    from infrastructure.state import active_account
    cage = Cage()
    
    cage.name = name
    cage.square_meters = meters
    cage.is_carpeted = carpeted
    cage.has_toys = has_toys
    cage.allow_dangerous_snakes = allow_dangerous
    cage.price = price
    
    cage.save()
    
    account = find_account_by_email(active_account.email)
    account.cage_ids.append(cage.id)
    account.save()
    
    return cage

def find_cages_by_owner(account: Owner) -> List[Cage]:
    return [Cage.objects(id=cage_id).first() for cage_id in account.cage_ids]


def add_available_date(selected_cage: Cage,
                           start_date: datetime.datetime,
                           days: int) -> Cage:
    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)
    cage = Cage.objects(id=selected_cage.id).first()
    cage.bookings.append(booking)
    cage.save()
    
    return cage
    
def add_snake(account, name, length, species, is_venemous) -> Snake:
    
    snake = Snake()
    snake.name = name
    snake.length = length
    snake.species = species
    snake.is_venomous = is_venemous
    snake.save()
    
    owner = find_account_by_email(account.email)
    owner.snake_ids.append(snake.id)
    owner.save()
    
    return snake


def get_snakes_for_owner(user_id: bson.ObjectId) -> List[Snake]:
    owner = Owner.objects(id=user_id).first()
    snakes = Snake.objects(id__in=owner.snake_ids).all()
    
    return list(snakes)


def get_available_cages(checkin: datetime, checkout: datetime, snake: Snake) -> List[Cage]:
    min_size = snake.length / 4
    query = Cage.objects() \
        .filter(square_meters__gte=min_size) \
        .filter(bookings__check_in_date__lte=checkin) \
        .filter(bookings__check_out_date__gte=checkout)
            
    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)
    
    cages = query.order_by('price', '-square_meters')
    
    final_cages = []
    for c in cages:
        for b in c.bookings:
            if b.check_in_date <= checkin and \
                b.check_out_date >= checkout and \
                b.guest_snake_id is None:
                final_cages.append(c)
    return final_cages


def book_cage(account, snake, cage, checkin, checkout) -> Booking:
    booking = None
    for b in cage.bookings:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
            booking = b
            break
    
    booking.guest_owner_id = account.id
    booking.guest_snake_id = snake.id
    booking.booked_date = datetime.datetime.now()
    
    cage.save()

def get_bookings_for_owner(email: str) -> List[Booking]:
    account = find_account_by_email(email)
    
    booked_cages =Cage.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')
    
    def map_cage_to_booking(cage, booking):
        booking.cage = cage
        return booking
    bookings = [
		map_cage_to_booking(cage, booking)
  		for cage in booked_cages
		for booking in cage.bookings
		if booking.guest_owner_id == account.id
	]
    
    return bookings
	
