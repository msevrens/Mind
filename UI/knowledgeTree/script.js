(function knowledgeTree() {

	var margin = {top: 20, right: 120, bottom: 20, left: 120},
		width = 960 - margin.right - margin.left,
		height = 600 - margin.top - margin.bottom;

	var treeLayout = d3.layout.tree().size([height, width]),
		diagonal = d3.svg.diagonal().projection(function(d) {return [d.y, d.x]}),
		duration = 750,
		i = 0,
		treeRoot;

	var svg = d3.select(".canvas-frame").append("svg")
		.attr("width", '100%')
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	function growTree(seedWord, json, depth) {

		var tree = {},
			used_words = [seedWord],
			max_depth = depth || 3,
			num_children = 3;

		if (!(seedWord in json)) {
			return {"name": "Seed word not found", "children": [{"name": "Please try another word"}]}
		}

		function growBranch(word, level) { 

			var children = [],
				num_twigs = num_children;

			if (!isNaN(word) || level == max_depth || !(word in json)) return;

			if (json[word].length < num_children) {
				num_twigs = json[word].length
			}

			for (var i=0; i<num_twigs; i++) {

				var cur_word = json[word][i]["w"],
					branch = {};

				if (used_words.indexOf(cur_word) > -1) continue;

				used_words.push(cur_word)
				branch["name"] = cur_word
				branch["fruit"] = json[word][i]["l"]

				children.push(branch)

			}

			for (var ii=0; ii<children.length; ii++) {
				num_children = Math.floor(Math.random() * 4) + 2
				var new_level = level + 1;
				if (new_level <= max_depth) {
					children[ii]["children"] = growBranch(children[ii]["name"], new_level)
				}
			}

			shuffle(children)
			return children

		}

		tree["name"] = seedWord
		tree["fruit"] = true
		tree["children"] = growBranch(seedWord, 0)
		tree.x0 = height / 2;
		tree.y0 = 0;

		return tree

	}

	function expandBranch(tree) {

		if (tree.children) {
			tree._children = tree.children;
			tree.children = null;
		} else {
			tree.children = tree._children;
			tree._children = null;
		}

  		updateTree(tree);

	}

	function updateTree(tree) {

		// Compute the new tree layout
		var nodes = treeLayout.nodes(treeRoot).reverse(),
			links = treeLayout.links(nodes);

		// Normalize for fixed-depth
		nodes.forEach(function(d) {d.y = d.depth * 180});

		// Update the nodes
		var node = svg.selectAll("g.node").data(nodes, function(d) {return d.id || (d.id = ++i)});

		// Enter any new nodes at the parent's previous position
		var nodeEnter = node.enter().append("g")
			.attr("class", "node")
			.attr("transform", function(d) { return "translate(" + tree.y0 + "," + tree.x0 + ")"; })
			.on("click", expandBranch);

		nodeEnter.append("circle")
			.attr("r", 1e-6)
			.style("fill", function(d) {
				var color = d._children ? "#88BD98" : "#88BD98"
				if (!d.fruit) color = "#50A2BF";
				return color
			});

		nodeEnter.append("text")
			.attr("x", function(d) { return d.children || d._children ? -10 : 10; })
			.attr("dy", ".35em")
			.attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
			.text(function(d) { return d.name; })
			.style("fill-opacity", 1e-6);

		// Transition nodes to their new position
		var nodeUpdate = node.transition()
			.duration(duration)
			.attr("transform", function(d) {return "translate(" + d.y + "," + d.x + ")"});

		nodeUpdate.select("circle")
			.attr("r", 4.5)
			.style("fill", function(d) {
				var color = d._children ? "#88BD98" : "#88BD98"
				if (!d.fruit) color = "#50A2BF";
				return color
			});

		nodeUpdate.select("text")
			.style("fill-opacity", 1);

		// Transition exiting nodes to the parent's new position
		var nodeExit = node.exit().transition()
			.duration(duration)
			.attr("transform", function(d) { return "translate(" + tree.y + "," + tree.x + ")"; })
			.remove();

		nodeExit.select("circle").attr("r", 1e-6);
		nodeExit.select("text").style("fill-opacity", 1e-6);

		// Update the links
		var link = svg.selectAll("path.link").data(links, function(d) {return d.target.id});

		// Enter any new links at the parent's previous position
		link.enter().insert("path", "g")
			.attr("class", "link")
			.attr("d", function(d) {
				var o = {x: tree.x0, y: tree.y0};
				return diagonal({source: o, target: o});
			});

		// Transition links to their new position
		link.transition()
			.duration(duration)
			.attr("d", diagonal);

		// Transition exiting nodes to the parent's new position
		link.exit().transition()
			.duration(duration)
			.attr("d", function(d) {
				var o = {x: tree.x, y: tree.y};
				return diagonal({source: o, target: o});
			}).remove();

		// Stash the old positions for transition
		nodes.forEach(function(d) {
			d.x0 = d.x;
			d.y0 = d.y;
		});

	}

	function shuffle(array) {

		var currentIndex = array.length, temporaryValue, randomIndex;

		while (0 !== currentIndex) {
			randomIndex = Math.floor(Math.random() * currentIndex);
			currentIndex -= 1;
			temporaryValue = array[currentIndex];
			array[currentIndex] = array[randomIndex];
			array[randomIndex] = temporaryValue;
		}

		return array;

	}

	function visualize(word, json) {

		treeRoot = growTree(word, json)

		function collapse(tree) {
			if (tree.children) {
				tree._children = tree.children;
				tree._children.forEach(collapse);
				tree.children = null;
			}
		}

		//treeRoot.children.forEach(collapse);
		updateTree(treeRoot);

	}

	function run(json) {

		d3.select("#build-tree").on("submit", function() {
			d3.event.preventDefault()
			svg.selectAll("*").remove()
			visualize(document.getElementById("seed-word").value, json)
			return false
		})

		treeRoot = growTree("word2vec", json, 3)
		updateTree(treeRoot);

	}

	var jsonPath = "../../data/word2vec_tree.json";

	d3.json(jsonPath, run);

})();