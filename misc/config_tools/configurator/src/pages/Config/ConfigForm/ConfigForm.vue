<template>
  <div style="position: relative">
    <b-button
        variant="primary"
        size="lg"
        class="deleteVM"
        @click="deleteVM"
        :class="{'d-none':currentActiveVMID===-1}"
    >
      <Icon>
        <Minus/>
      </Icon>
      Delete VM
    </b-button>
  </div>
  <b-tabs>
    <b-tab title="Basic Parameters">
      <p>
        <text style="color: red">*</text>
        are required fields
      </p>
      <VueForm
          v-model="currentFormData"
          :form-props="formProps"
          :ui-schema="uiSchema"
          :schema="currentFormSchema.BasicConfigType"
          @change="dataChange"
      >
        <template>

        </template>
      </VueForm>
    </b-tab>
    <b-tab title="Advanced Parameters">
      <p>
        <text style="color: red">*</text>
        are required fields
      </p>
      <VueForm
          v-model="currentFormData"
          :form-props="formProps"
          :ui-schema="uiSchema"
          :schema="currentFormSchema.AdvancedConfigType"
          @change="dataChange"
      >
        <template>

        </template>
      </VueForm>
    </b-tab>
  </b-tabs>
</template>

<script>
import VueForm, {i18n} from "@lljj/vue3-form-naive"
import {Icon} from "@vicons/utils";
import {Minus} from "@vicons/fa"
import localizeEn from 'ajv-i18n/localize/en';


i18n.useLocal(localizeEn);
export default {
  name: "ConfigForm",
  components: {Icon, Minus, VueForm},
  emits: ['scenarioConfigFormDataUpdate', 'deleteVM'],
  props: {
    currentActiveVMID: {type: Number},
    currentFormSchema: {type: Object},
    currentFormData: {type: Object}
  },
  data() {
    return {
      formProps: {
        "inline": false,
        "inlineFooter": false,
        "labelPosition": "left",
        "labelWidth": "300px",
        "labelSuffix": "："
      },
      uiSchema: {}
    };
  },
  methods: {
    deleteVM() {
      this.$emit('deleteVM')
    },
    dataChange({newValue, oldValue}) {
      let newID = newValue.hasOwnProperty('@id') ? newValue['@id'] : -1;
      let oldID = oldValue.hasOwnProperty('@id') ? oldValue['@id'] : -1;
      if (newID === oldID) {
        this.$emit('scenarioConfigFormDataUpdate', newID, newValue)
      }
      // this.$emit('update:scenarioData', this.formData)
    }
  }
}
</script>

<style>
.nav-tabs .nav-link {
  /*noinspection CssNoGenericFontName*/
  font-family: Roboto;
  font-style: normal;
  font-weight: 500;
  font-size: 22px;
  line-height: 26px;

  background: #E1F2EF;
  border: 1px solid #007B81;
  box-sizing: border-box;
  box-shadow: inset 0 -1px 0 #D7D7D7;
  border-radius: 5px 5px 0 0;
  border-bottom: none;

  color: #007B81;
  margin-right: 4px;
  padding: 1rem 1.5rem;
}

.nav-tabs .nav-link.active {
  mix-blend-mode: normal;
  border: 1px solid #373A77;
  border-bottom: none;
  box-sizing: border-box;
  border-radius: 5px 5px 0 0;


  font-weight: 600;

  color: #373A77;
}

.tab-pane {
  margin-top: -2px;
  border: 1px solid rgb(55, 58, 119);
  box-sizing: border-box;
  border-radius: 0 5px 5px;
  padding: 2rem;
}

.nav-tabs {
  border-bottom: none;
}

.deleteVM {
  height: 52px;
  max-width: 210px;
  width: 100%;
  position: absolute;
  right: 0;
}
</style>