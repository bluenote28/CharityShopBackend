from ebay.models import Charity
from ebay.serializers import CharitySerializer

def deleteCharity(id):
     
    try: 
        charity = Charity.objects.get(id=id)
        charity.delete()
        return "Success"
    except Exception as e:
        print(f"Error deleting charity: {e}")
        return e


def addCharity(charity_data):

    serializer = CharitySerializer(data=charity_data)
    if serializer.is_valid():
        serializer.save()
        return "Success"
    else:
        return "Failure"
