folder = 'F:\MTA_DATA\ringworld\100000';
behavior = 0.25;
target = 0.15;
dirOutput = dir(fullfile(folder, '*'));
subfolders = {dirOutput.name}';
subfolders(1: 2) = [];
MTA_VALUES = {};
CURVES = [];
LEGENDS = {};
KAPPAS = [];
VALUES = [];
for i = 1: length(subfolders)
    subfoler = subfolders{i};
    dirOutput = dir(fullfile(folder, subfoler, '*'));
    filenames = {dirOutput.name}';
    reduce_index = [];
    for j = 1: numel(filenames)
        if isempty(strfind(filenames{j}, ['behavior_', num2str(behavior)])) || isempty(strfind(filenames{j}, ['target_', num2str(target)]))
            reduce_index = [reduce_index, j];
        end
    end
    filenames(reduce_index) = [];
    try
        filename = filenames{1};
        loaded = load(fullfile(folder, subfoler, filename));
    catch ME
        continue;
    end
    KAPPAS = [KAPPAS, str2double(subfoler)];
    VALUES = [VALUES, mean(MEAN(end - 5 : end))];
% 	if strcmp(subfoler, '0.2') || strcmp(subfoler, '0.1')
%         continue; 
%     end
    [X, MEAN, INTERVAL] = get_statistics(loaded.error_value_mta, 201, true);
    [CURVE, ~] = band_drawer(X, MEAN, INTERVAL);
    CURVES = [CURVES, CURVE];
    LEGEND = sprintf('\\kappa=%s', subfoler);
    LEGENDS = [LEGENDS, LEGEND];
end

L = legend(CURVES, LEGENDS);
set(L, 'FontName', 'Book Antiqua', 'FontSize', 14);
set(L, 'Location', 'southwest');
set(gca, 'xscale', 'log');
set(gca, 'yscale', 'log');
axis([1, inf, 0, inf]);
drawnow;

figure;
plot(KAPPAS, VALUES, 'LineWidth', 2);
set(gca, 'xscale', 'log');
% set(gca, 'yscale', 'log');
axis([0, inf, 0, inf]);
drawnow;