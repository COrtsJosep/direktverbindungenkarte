var map = L.map('map').setView([46.798449, 8.231879], 9);

L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.{ext}', {
	minZoom: 0,
	maxZoom: 20,
	attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	ext: 'png'
}).addTo(map);

L.controlCredits({
    imageurl: 'public/GitHub_Invertocat_Black.png',
    tooltip: 'Made by COrtsJosep',
    width: '45px',
    height: '45px',
    expandcontent: 'Made for fun by COrtsJosep, hosted at<br/><a href="https://github.com/COrtsJosep/direktverbindungskarte" target="_blank">COrtsJosep/direktverbindungskarte</a>',
    imagealt: 'Could not load icon'
}).addTo(map);

var notifications = L.control.notifications({ 
    className: 'modern',
    timeout: 5000,
    closable: false,
    dismissable: true
}).addTo(map);

notifications.info('Info', 'Click on a train station to discover where you can travel to with a direct connection.');

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

// Idea of the program: 
// Initially the layer with all stations (as dots) is loeaded onto the map.
// Hoovering reveals the name of the station. 
// Clicking on a station removes the layer with all stations and reveals the
// network of the clicked station (see next comment).
var allDienstStelleLayer = new L.GeoJSON.AJAX("src/assets/dienststellen.geojson", {
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, dienstStelleStyle);
    },
    onEachFeature: function(feature, layer) {
        if (feature.properties && feature.properties.designationOfficial && feature.properties.number) {
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

// After clicking on a station, two layers are added: the layer with the reachable
// railroad network linestrings, and the layer with the reachable stations.
// Clicking on the same station again returns to the initial state of the webpage.
// Clicking on a different station switches the focus onto that station (removes
// the two layers and adds the reachable stations + network of the newly selected
// station.
function addNetwork(number) {
    var railRoadsLayer = new L.GeoJSON.AJAX(`src/assets/reachable_net_per_station/${number}.geojson`, {
        style: railRoadsStyle,
        onEachFeature: function(feature, layer) {
            layer.on({
                'add': function(){layer.bringToBack()}
            });
            
        }
    });
    railRoadsLayer.addTo(map);
    
    var reachableDienstStelleLayer = new L.GeoJSON.AJAX(`src/assets/reachable_stations_per_station/${number}.geojson`, {
    pointToLayer: function (feature, latlng) {
        if (feature.properties && feature.properties.number && feature.properties.number == number) {
            return L.circleMarker(latlng, selectedDienstStelleStyle);
        } else if (feature.properties && feature.properties.number && feature.properties.number != number) {
            return L.circleMarker(latlng, dienstStelleStyle);
        }
    },
    onEachFeature: function(feature, layer) {
        if (feature.properties && feature.properties.designationOfficial && feature.properties.number) {
            layer.on('mouseover', function(e) {
                var popup = L.popup({ closeButton: false, minWidth: 0 }).setContent(feature.properties.designationOfficial);
                layer.bindPopup(popup).openPopup();
            });
            layer.on('mouseout', function(e) {
                layer.closePopup();
            });
            layer.on('click', function(e) {
                if (feature.properties.number == number) {
                    // return to inital state
                    map.removeLayer(railRoadsLayer);
                    map.removeLayer(reachableDienstStelleLayer);
                    allDienstStelleLayer.addTo(map);
                } else {
                    // re-focus on newly selected station
                    map.removeLayer(railRoadsLayer);
                    map.removeLayer(reachableDienstStelleLayer);
                    addNetwork(feature.properties.number);
                }
            });
        }
    }
    });
    reachableDienstStelleLayer.addTo(map);
    
    notifications.info('Info', 'Click on another train station to discover where you can travel to with a direct connection, or click on the same one again to deselect it.');
}
