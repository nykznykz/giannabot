from datetime import datetime
from dotenv import load_dotenv
import os
from singapore_data import LTADataMallBus
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Type
import pandas as pd
import numpy as np

load_dotenv()

class BusQueryInput(BaseModel):
    bus_stop_code: str = Field(description="The 5-digit bus stop code to query")

class BusQueryTool(BaseTool):
    name: str = "bus_arrival_query"
    description: str = "Query bus arrival information for a specific bus stop in Singapore. Returns formatted arrival times, bus types, and passenger load information."
    args_schema: Type[BaseModel] = BusQueryInput

    def __init__(self, **kwargs):
        """Initialize the bus query tool."""
        super().__init__(**kwargs)
        self._client = LTADataMallBus()
        
    def format_time(self, estimated_arrival: str) -> str:
        """Format the estimated arrival time to a more readable format."""
        if not estimated_arrival:
            return "No arrival time available"
        
        # Parse the arrival time with timezone
        arrival_time = datetime.fromisoformat(estimated_arrival)
        # Get current time with the same timezone
        now = datetime.now(arrival_time.tzinfo)
        minutes_away = (arrival_time - now).total_seconds() / 60
        
        if minutes_away < 0:
            return "Arrived"
        elif minutes_away < 1:
            return "Arriving"
        else:
            return f"{int(minutes_away)} min"

    def format_load(self, load: str) -> str:
        """Format the bus load to a more readable format."""
        load_map = {
            'SEA': 'Seats Available',
            'SDA': 'Standing Available',
            'LSD': 'Limited Standing'
        }
        return load_map.get(load, load)

    def format_bus_type(self, bus_type: str) -> str:
        """Format the bus type to a more readable format."""
        type_map = {
            'SD': 'Single Deck',
            'DD': 'Double Deck',
            'BD': 'Bendy'
        }
        return type_map.get(bus_type, bus_type)

    def _run(self, bus_stop_code: str) -> str:
        """
        Query bus arrival information for a specific bus stop.
        
        Args:
            bus_stop_code (str): The 5-digit bus stop code
            
        Returns:
            str: A formatted string containing bus arrival information
        """
        try:
            bus_info = self._client.get_next_bus_info_concise(bus_stop_code)
            
            if not bus_info:
                return "No bus services available at this stop."
            print(bus_info)
            formatted_info = []
            for service_no, arrival_time, load, bus_type in bus_info:
                formatted_info.append(
                    f"Bus {service_no} ({self.format_bus_type(bus_type)}): "
                    f"Arriving in {self.format_time(arrival_time)}, "
                    f"{self.format_load(load)}"
                )
            
            return f"Bus Stop {bus_stop_code}:\n" + "\n".join(formatted_info)
            
        except Exception as e:
            return f"Error querying bus information: {str(e)}"

    async def _arun(self, bus_stop_code: str) -> str:
        """Async version of the tool."""
        return self._run(bus_stop_code)
    

class NearestBusStopQueryInput(BaseModel):
    target_lat: float = Field(description="The latitude of the query location")
    target_lon: float = Field(description="The longitude of the query location")

class NearestBusStopQueryTool(BaseTool):
    name: str = "nearest_bus_stop_query"
    description: str = "Query nearest bus stops given a latitude and longitude. Returns the bus stop code, description and distance in km."
    args_schema: Type[BaseModel] = NearestBusStopQueryInput

    def _run(self, target_lat: float, target_lon: float) -> str:
        """
        Query bus stop information for a specific bus stop.
        
        Args:
            target_lat (float): The latitude of the query location
            target_lon (float): The longitude of the query location
        """
        nearest_stops = get_nearest_stops(target_lat, target_lon)
        return nearest_stops
    

def get_nearest_stops(target_lat, target_lon):
    # Your bus stop dataframe (e.g., all_busstops)
    # Let's say it's already loaded and named `all_busstops`
    all_busstops = pd.read_csv('data/all_busstops.csv')
    
    # Target coordinates
    
    # Convert degrees to radians
    lat_rad = np.radians(all_busstops['Latitude'])
    lon_rad = np.radians(all_busstops['Longitude'])
    target_lat_rad = np.radians(target_lat)
    target_lon_rad = np.radians(target_lon)
    
    # Haversine formula
    dlat = lat_rad - target_lat_rad
    dlon = lon_rad - target_lon_rad
    
    a = np.sin(dlat/2.0)**2 + np.cos(target_lat_rad) * np.cos(lat_rad) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    earth_radius_km = 6371
    distances = earth_radius_km * c
    
    # Add distance to DataFrame
    all_busstops['Distance_km'] = distances
    
    # Get N nearest bus stops
    N = 5
    nearest_stops = all_busstops.nsmallest(N, 'Distance_km')
    
    nearest_stops = nearest_stops[['BusStopCode', 'Description', 'Distance_km']]
    return format_nearest_stops_markdown(nearest_stops,target_lat, target_lon)

def format_nearest_stops_markdown(nearest_stops_df, latitude, longitude):
    markdown = f"### 🚌 Nearest Bus Stops\n"
    markdown += f"**Reference Point:**  \nLatitude: `{latitude}`  \nLongitude: `{longitude}`  \n\n"
    markdown += f"**Top {len(nearest_stops_df)} closest bus stops:**\n\n"

    for idx, row in nearest_stops_df.iterrows():
        markdown += (
            f"{nearest_stops_df.index.get_loc(idx)+1}. **{row['Description']}**\n"
            f"   - 🆔 Bus Stop Code: `{row['BusStopCode']}`\n"
            f"   - 📏 Distance: `{row['Distance_km']:.3f} km`\n\n"
        )

    return markdown

# Example usage
if __name__ == "__main__":
    tool = BusQueryTool()
    result = tool.run("52071")
    print(result) 
    tool = NearestBusStopQueryTool()
    result = tool.run({
    "target_lat": 1.330638,
    "target_lon": 103.842668
})
    print(result)