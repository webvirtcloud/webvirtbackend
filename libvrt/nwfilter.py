from .connection import wvmConnect


class wvmNWfilter(wvmConnect):
    def get_nwfilters(self):
        return self.wvm.listNWFilters()

    def get_nwfilter(self, name):
        return self.wvm.nwfilterLookupByName(name)

    def get_nwfilter_xml(self, name):
        nw = self.get_nwfilter(name)
        return nw.XMLDesc()

    def delete_nwfilter(self, name):
        nw = self.get_nwfilter(name)
        nw.undefine()

    def create_nwfilter(self, xml):
        self.wvm.nwfilterDefineXML(xml)
