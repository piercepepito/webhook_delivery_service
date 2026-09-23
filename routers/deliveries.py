from db import LocalSession

from models import Deliveries

def post_new_delivery(delivery_payload):
    new_delivery = Deliveries(**delivery_payload)

    with LocalSession() as session:
        session.add(new_delivery)
        session.commit()
        session.refresh(new_delivery)

    return new_delivery

    
#def patch using id
