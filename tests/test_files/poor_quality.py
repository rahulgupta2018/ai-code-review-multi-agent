
def process_user_data(data):
    # Poor quality: deep nesting, no documentation, complex logic
    if data:
        if data.get("name"):
            if len(data["name"]) > 0:
                if data.get("email"):
                    if "@" in data["email"]:
                        if data.get("age"):
                            if data["age"] > 0:
                                if data.get("preferences"):
                                    if isinstance(data["preferences"], dict):
                                        if "theme" in data["preferences"]:
                                            return True
    return False

def calculate_metrics(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t):
    # Poor quality: too many parameters, no documentation, complex calculation
    result = a + b + c + d + e + f + g + h + i + j
    result = result * k + l - m + n / o
    for x in range(100):
        if x % 2 == 0:
            result += x
        else:
            result -= x
            for y in range(50):
                result += y * 2
                if y > 25:
                    for z in range(10):
                        result += z
    return result

def duplicate_logic_1(x):
    # Duplicate code pattern
    result = x * 2
    result = result + 10
    result = result / 3
    return result

def duplicate_logic_2(y):
    # Duplicate code pattern (same as above)
    result = y * 2
    result = result + 10
    result = result / 3
    return result

class DataProcessor:
    def __init__(self):
        # Poor quality: no documentation, unclear variable names
        self.x = 1
        self.y = 2
        self.data = {}
        
    def process(self,data):
        # Poor quality: no documentation, minimal logic
        return data+1
    
    def validate(self,input):
        # Poor quality: always returns True
        return True
