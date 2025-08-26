import React from 'react';

const Loader = ({ label = 'Загрузка...' }) => {
	return (
		<div className="flex items-center gap-3 text-gray-500">
			<div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
			<span>{label}</span>
		</div>
	);
};

export default Loader;
