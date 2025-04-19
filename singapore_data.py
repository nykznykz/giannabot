import requests
import os
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class LTADataMallBus:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LTA DataMall API client.
        
        Args:
            api_key (str, optional): Your LTA DataMall API key. If not provided,
                                   will try to get from environment variable LTA_API_KEY.
        """
        self.api_key = api_key or os.getenv('LTA_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through LTA_API_KEY environment variable")
        
        self.base_url = "http://datamall2.mytransport.sg/ltaodataservice"
        self.headers = {
            'AccountKey': self.api_key,
            'accept': 'application/json'
        }

    def get_bus_arrival(self, bus_stop_code: str, service_no: Optional[str] = None) -> Dict:
        """
        Get bus arrival timings for a specific bus stop.
        
        Args:
            bus_stop_code (str): 5-digit bus stop code
            service_no (str, optional): Bus service number. If not provided, returns all services.
        
        Returns:
            Dict: Response containing bus arrival information
        """
        endpoint = f"{self.base_url}/BusArrivalv2"
        params = {'BusStopCode': bus_stop_code}
        if service_no:
            params['ServiceNo'] = service_no
            
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_bus_stops(self, skip: int = 0) -> Dict:
        """
        Get list of bus stops.
        
        Args:
            skip (int): Number of records to skip (for pagination)
        
        Returns:
            Dict: Response containing bus stop information
        """
        endpoint = f"{self.base_url}/BusStops"
        params = {'$skip': skip}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_bus_routes(self, skip: int = 0) -> Dict:
        """
        Get list of bus routes.
        
        Args:
            skip (int): Number of records to skip (for pagination)
        
        Returns:
            Dict: Response containing bus route information
        """
        endpoint = f"{self.base_url}/BusRoutes"
        params = {'$skip': skip}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_bus_services(self, skip: int = 0) -> Dict:
        """
        Get list of bus services.
        
        Args:
            skip (int): Number of records to skip (for pagination)
        
        Returns:
            Dict: Response containing bus service information
        """
        endpoint = f"{self.base_url}/BusServices"
        params = {'$skip': skip}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_next_bus_info_concise(self, bus_stop_code: str, service_no: Optional[str] = None) -> Dict:
        """
        Get next bus arrival timings for a specific bus stop.
        
        Args:
            bus_stop_code (str): 5-digit bus stop code
            service_no (str, optional): Bus service number. If not provided, returns all services.
        
        Returns:
            Dict: Response containing bus arrival information
        """
        services = self.get_bus_arrival(bus_stop_code)['Services']
        return[(service['ServiceNo'], service['NextBus']['EstimatedArrival'], service['NextBus']['Load'], service['NextBus']['Type']) for service in services]
    


if __name__ == "__main__":
    # Initialize the client
    client = LTADataMallBus()  # Will use LTA_API_KEY from environment

    # Get bus arrival timings for a specific stop
    bus_stop_code = 52071  # Example bus stop code
    arrivals = client.get_bus_arrival(bus_stop_code)

    # Get arrivals for a specific bus service
    # arrivals = client.get_bus_arrival(bus_stop_code, service_no="123")

    # Get list of bus stops
    bus_stops = client.get_bus_stops()['value']
    print(bus_stops)
    # print({bus_stop['Description']: bus_stop['BusStopCode'] for bus_stop in bus_stops})
    # print(client.get_next_bus_info_concise(bus_stop_code))

