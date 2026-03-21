var map = L.map('map').setView([46.798449, 8.231879], 9);

L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.{ext}', {
	minZoom: 0,
	maxZoom: 20,
	attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	ext: 'png'
}).addTo(map);

var dienstStelleStyle = {
    radius: 7.5,
    fillColor: "#FFFFFF",
    color: "#5A5A5A",
    weight: 5,
    opacity: 1,
    fillOpacity: 1
};

var selectedDienstStelleStyle = {
    radius: 7.5,
    fillColor: "#FFFFFF",
    color: "#FF0000",
    weight: 5,
    opacity: 1,
    fillOpacity: 1
};

var railRoadsStyle = {
    "color": "#FF0000",
    "weight": 5,
    "opacity": 1
};

function addNetwork(number) {
    var railRoadsLayer = new L.GeoJSON.AJAX(`src/python-demo/reachable_net_readyfiles/${number}.geojson`, {
        style: railRoadsStyle,
        onEachFeature: function(feature, layer) {
            layer.on({
                'add': function(){layer.bringToBack()}
            })
        }
    });
    railRoadsLayer.addTo(map);
    
    var reachableDienstStelleLayer = new L.GeoJSON.AJAX(`src/python-demo/reachable_stations_readyfiles/${number}.geojson`, {
    pointToLayer: function (feature, latlng) {
        if (feature.properties && feature.properties.number && feature.properties.number == number) {
            return L.circleMarker(latlng, selectedDienstStelleStyle);
        } else if (feature.properties && feature.properties.number && feature.properties.number != number) {
            return L.circleMarker(latlng, dienstStelleStyle);
        }
    },
    onEachFeature: function(feature, layer) {
        if (feature.properties && feature.properties.designationOfficial && feature.properties.number) {
            // Show popup on hover
            layer.on('mouseover', function(e) {
                var popup = L.popup({ closeButton: false, minWidth: 0 }).setContent(feature.properties.designationOfficial);
                layer.bindPopup(popup).openPopup();
            });
            layer.on('mouseout', function(e) {
                layer.closePopup();
            });
            layer.on('click', function(e) {
                if (feature.properties.number == number) {
                    map.removeLayer(railRoadsLayer);
                    map.removeLayer(reachableDienstStelleLayer);
                    allDienstStelleLayer.addTo(map);
                } else {
                    map.removeLayer(railRoadsLayer);
                    map.removeLayer(reachableDienstStelleLayer);
                    addNetwork(feature.properties.number);
                }
            });
        }
    }
    });
    reachableDienstStelleLayer.addTo(map);
}

var allDienstStelleLayer = new L.GeoJSON.AJAX("src/python-demo/dienststellen.geojson", {
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, dienstStelleStyle);
    },
    onEachFeature: function(feature, layer) {
        if (feature.properties && feature.properties.designationOfficial && feature.properties.number) {
            // Show popup on hover
            layer.on('mouseover', function(e) {
                var popup = L.popup({ closeButton: false, minWidth: 0 }).setContent(feature.properties.designationOfficial);
                layer.bindPopup(popup).openPopup();
            });
            layer.on('mouseout', function(e) {
                layer.closePopup();
            });
            layer.on('click', function(e) {
                map.removeLayer(allDienstStelleLayer);
                addNetwork(feature.properties.number);
            });
        }
    }
});


allDienstStelleLayer.addTo(map);
