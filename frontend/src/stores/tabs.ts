import { create } from 'zustand';

export interface TabItem {
  key: string;
  label: string;
  closable: boolean;
}

interface TabState {
  tabs: TabItem[];
  activeKey: string;
  addTab: (key: string, label: string) => void;
  removeTab: (targetKey: string) => string | null;
  setActiveKey: (key: string) => void;
  resetTabs: () => void;
}

export const useTabStore = create<TabState>((set, get) => ({
  tabs: [],
  activeKey: '',

  addTab: (key, label) => {
    const { tabs } = get();
    const exists = tabs.find((t) => t.key === key);
    if (!exists) {
      set({ tabs: [...tabs, { key, label, closable: true }] });
    }
    set({ activeKey: key });
  },

  removeTab: (targetKey) => {
    const { tabs, activeKey } = get();
    const index = tabs.findIndex((t) => t.key === targetKey);
    const newTabs = tabs.filter((t) => t.key !== targetKey);

    let nextKey: string | null = null;
    if (activeKey === targetKey && newTabs.length > 0) {
      nextKey = index >= newTabs.length ? newTabs[newTabs.length - 1].key : newTabs[index].key;
    }

    set({
      tabs: newTabs,
      activeKey: nextKey || (newTabs.length > 0 ? newTabs[newTabs.length - 1].key : ''),
    });
    return nextKey;
  },

  setActiveKey: (key) => set({ activeKey: key }),

  resetTabs: () => set({ tabs: [], activeKey: '' }),
}));
