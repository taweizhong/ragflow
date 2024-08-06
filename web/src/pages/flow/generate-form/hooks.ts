import get from 'lodash/get';
import { useCallback, useMemo } from 'react';
import { v4 as uuid } from 'uuid';
import { Operator } from '../constant';
import { IGenerateParameter } from '../interface';
import useGraphStore from '../store';

// exclude nodes with branches
const ExcludedNodes = [Operator.Categorize, Operator.Relevant];

export const useBuildComponentIdSelectOptions = (nodeId?: string) => {
  const nodes = useGraphStore((state) => state.nodes);

  const options = useMemo(() => {
    return nodes
      .filter(
        (x) =>
          x.id !== nodeId && !ExcludedNodes.some((y) => y === x.data.label),
      )
      .map((x) => ({ label: x.data.name, value: x.id }));
  }, [nodes, nodeId]);

  return options;
};

export const useHandleOperateParameters = (nodeId: string) => {
  const { getNode, updateNodeForm } = useGraphStore((state) => state);
  const node = getNode(nodeId);
  const dataSource: IGenerateParameter[] = useMemo(
    () => get(node, 'data.form.parameters', []) as IGenerateParameter[],
    [node],
  );

  const handleComponentIdChange = useCallback(
    (row: IGenerateParameter) => (value: string) => {
      const newData = [...dataSource];
      const index = newData.findIndex((item) => row.id === item.id);
      const item = newData[index];
      newData.splice(index, 1, {
        ...item,
        component_id: value,
      });

      updateNodeForm(nodeId, { parameters: newData });
    },
    [updateNodeForm, nodeId, dataSource],
  );

  const handleRemove = useCallback(
    (id?: string) => () => {
      const newData = dataSource.filter((item) => item.id !== id);
      updateNodeForm(nodeId, { parameters: newData });
    },
    [updateNodeForm, nodeId, dataSource],
  );

  const handleAdd = useCallback(() => {
    updateNodeForm(nodeId, {
      parameters: [
        ...dataSource,
        {
          id: uuid(),
          key: '',
          component_id: undefined,
        },
      ],
    });
  }, [dataSource, nodeId, updateNodeForm]);

  const handleSave = (row: IGenerateParameter) => {
    const newData = [...dataSource];
    const index = newData.findIndex((item) => row.id === item.id);
    const item = newData[index];
    newData.splice(index, 1, {
      ...item,
      ...row,
    });

    updateNodeForm(nodeId, { parameters: newData });
  };

  return {
    handleAdd,
    handleRemove,
    handleComponentIdChange,
    handleSave,
    dataSource,
  };
};
