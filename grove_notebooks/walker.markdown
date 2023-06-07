``` js
api = getApi("0.0.227")
```

``` js
data = Object() 
```

``` js
function lerp_nodes(node1, node2, t) {
  let lat1 = node1.properties['latitude']
  let lat2 = node2.properties['latitude']
  let lng1 = node1.properties['longitude']
  let lng2 = node2.properties['longitude']
  
  let agent_lat = lat1 + (lat2 - lat1) * t;
  let agent_lng = lng1 + (lng2 - lng1) * t;
  return [agent_lat, agent_lng]
}
```

``` js
viewof map1 = {
  const container = yield htl.html`<div style="height: 500px;">`;
  const vancouver_pos = [49.25, -123]; 
  const map = L.map(container).setView(vancouver_pos, 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© <a href=https://www.openstreetmap.org/copyright>OpenStreetMap</a> contributors"
  }).addTo(map);
  
  data.map = map; 
}
```

``` js
function get_neighbor_and_length(graph, junction) {
  let neighbors = graph.findNeighbors(junction.id).filter((neighbor) => neighbor.neighbor.category = "Junction");
  if (neighbors.length == 0) return [junction, 0];
  
  let index = Math.floor(Math.random() * neighbors.length);
  let junction_2 = neighbors[index].neighbor;
  let length = neighbors[index].connectedEdge.properties.length_metres;
  return [junction_2, length]
}
```

``` js
Grove.AsyncButton({
  label: "Run Agent", 
  onClick: pathWalker
})
```

``` js
async function randomWalker () {
  data.running = true
  if (data.agent) {
  	data.agent.removeFrom(data.map);
    data.j1.removeFrom(data.map);
    data.j2.removeFrom(data.map);
  }
  
  let graph = api.getLayoutGraph();
  
  let junctions = graph.getVisibleNodes().filter(api.nodesByCategory("Junction"));
  let index = Math.floor(Math.random() * junctions.length);
  let junction_1 = junctions[index];
  let [junction_2, length] = get_neighbor_and_length(graph, junction_1);
  
  let begin_time = performance.now() / 1000;
  let time = begin_time;
  let meters_per_second = 30;
  
  let agent_pos = lerp_nodes(junction_1, junction_2, 0);
  let agent = L.marker(agent_pos).addTo(data.map);
  data.agent = agent;
 
  data.j1 = L.circleMarker([junction_1.properties.latitude, junction_1.properties.longitude]).addTo(data.map);
  data.j2 = L.circleMarker([junction_2.properties.latitude, junction_2.properties.longitude]).addTo(data.map);
  
  while (data.running) {
    time = performance.now() / 1000 - begin_time;
    
    if (time * meters_per_second / length >= 1) {
      begin_time += length / meters_per_second;
      time = performance.now() / 1000 - begin_time;
      junction_1 = junction_2;
      [junction_2, length] = get_neighbor_and_length(graph, junction_1);
      
      data.j1.setLatLng([junction_1.properties.latitude, junction_1.properties.longitude]);
      data.j2.setLatLng([junction_2.properties.latitude, junction_2.properties.longitude]);
    }
    
    agent_pos = lerp_nodes(junction_1, junction_2, time * meters_per_second / length);
    agent.setLatLng(agent_pos);
    await api.sleep(20);
  }
}
```

``` js
async function pathWalker () {
  data.running = true
  if (data.agent) {
  	data.agent.removeFrom(data.map);
    data.j1.removeFrom(data.map);
    data.j2.removeFrom(data.map);
  }
  
  let graph = api.getLayoutGraph();
  
  let junctions = graph.getVisibleNodes().filter(api.nodesByCategory("Junction"));
  if (junctions.length == 0) return;
  
  let start_junction = junctions[Math.floor(Math.random() * junctions.length)];
  let end_junction = junctions[Math.floor(Math.random() * junctions.length)];
  
  data.j1 = L.circleMarker([start_junction.properties.latitude, start_junction.properties.longitude]).addTo(data.map);
  data.j2 = L.circleMarker([end_junction.properties.latitude, end_junction.properties.longitude]).addTo(data.map);
  
  console.log("Running dijkstra")
  let paths = api.dijkstra(graph, {sourceId: start_junction.id, targetId: end_junction.id, weightProperty: "length_meters"});
  console.log("Dijkstra finished")
  if (paths.length == 0 || paths[0].length < 2) return;
  
  let path = paths[0];
  let path_index = 0;
  
  let junction_1 = graph.getNode(path[path_index].nodeId);
  let junction_2 = graph.getNode(path[path_index + 1].nodeId);
  let length = graph.getEdge(path[path_index].edgeId).properties.length_metres;
  
  let begin_time = performance.now() / 1000;
  let time = begin_time;
  let meters_per_second = 30;
  
  let agent_pos = lerp_nodes(junction_1, junction_2, 0);
  let agent = L.marker(agent_pos).addTo(data.map);
  data.agent = agent;
 
  
  
  while (data.running) {
    time = performance.now() / 1000 - begin_time;
    
    if (time * meters_per_second / length >= 1) {
      begin_time += length / meters_per_second;
      time = performance.now() / 1000 - begin_time;
      path_index += 1;
      if (path_index >= path.length - 1) {
        data.running = false;
        break;
      }
      junction_1 = junction_2;
      junction_2 = graph.getNode(path[path_index + 1].nodeId);
      length = graph.getEdge(path[path_index].edgeId).properties.length_metres;
      
      //data.j1.setLatLng([junction_1.properties.latitude, junction_1.properties.longitude]);
      //data.j2.setLatLng([junction_2.properties.latitude, junction_2.properties.longitude]);
    }
    
    agent_pos = lerp_nodes(junction_1, junction_2, time * meters_per_second / length);
    agent.setLatLng(agent_pos);
    await api.sleep(20);
  }
}
```

``` js
Grove.Button({
  label: "Stop Agent",
  onClick: () => {
    data.running = false;
  }
})
```
