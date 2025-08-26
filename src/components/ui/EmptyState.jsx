import React from 'react';

const EmptyState = ({ title = 'Нет данных', description = 'Попробуйте изменить фильтры или добавить новый элемент.', action }) => {
	return (
		<div className="text-center py-12 text-gray-600">
			<div className="text-4xl mb-2">📭</div>
			<h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
			<p className="text-gray-500 mb-4">{description}</p>
			{action}
		</div>
	);
};

export default EmptyState;
