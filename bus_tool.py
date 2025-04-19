from typing import Dict, List, Optional, Type
from datetime import datetime
from dotenv import load_dotenv
import os
from singapore_data import LTADataMallBus
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

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

# Example usage
if __name__ == "__main__":
    tool = BusQueryTool()
    result = tool.run("52071")
    print(result) 